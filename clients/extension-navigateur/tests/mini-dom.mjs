/*
 * Un DOM minimal, pour eprouver le lecteur hors navigateur.
 *
 * ------------------------------------------------------------------
 * Pourquoi ce fichier existe, et ce qu'il ne pretend pas etre
 * ------------------------------------------------------------------
 *
 * Le JavaScript du plugin n'avait aucun test rejouable: il n'avait ete eprouve
 * qu'une fois, a la main, injecte dans une page reelle. Une verification qui ne
 * se rejoue pas ne protege de rien - elle dit que le code marchait ce jour-la.
 *
 * Ce module fournit donc juste assez de DOM pour que `lecteur.js` s'execute
 * sous Node: `querySelector`, `querySelectorAll`, `children`, `tagName`,
 * `textContent`, `classList.contains`, `getAttribute`. Rien de plus.
 *
 * **Ce n'est pas un navigateur, et c'est assume.** Un moteur reel gere les
 * balises implicites, les documents mal formes, les espaces de noms. Les
 * gabarits de test sont donc ecrits en HTML simple et bien forme, ce qui est
 * exactement le cas d'usage: on eprouve la LOGIQUE du lecteur - reconnaitre un
 * groupe, fusionner deux liens, ignorer un sous-total - pas la tolerance d'un
 * analyseur syntaxique.
 *
 * Le garde-fou contre la derive de ce raccourci est ailleurs, et il est solide:
 * `test_extension_javascript.py` fait tourner le lecteur JS **et** le lecteur
 * Python sur les memes gabarits, et exige qu'ils rendent la meme chose. Si ce
 * mini-DOM se mettait a mentir, les deux cesseraient de coincider.
 */

const AUTO_FERMANTS = new Set(["br", "hr", "img", "input", "meta", "link", "source"]);

class Noeud {
  constructor(tag, attrs = {}) {
    this.tagName = tag.toUpperCase();
    this.nomBalise = tag.toLowerCase();
    this.attrs = attrs;
    this.enfants = [];
    this.texteBrut = "";
    this.parent = null;
  }

  get children() {
    return this.enfants.filter((e) => e.tagName !== "#TEXTE");
  }

  get textContent() {
    if (this.tagName === "#TEXTE") return this.texteBrut;
    return this.enfants.map((e) => e.textContent).join("");
  }

  get className() {
    return this.attrs["class"] || "";
  }

  get classList() {
    const classes = this.className.split(/\s+/).filter(Boolean);
    return { contains: (c) => classes.includes(c) };
  }

  getAttribute(nom) {
    return Object.prototype.hasOwnProperty.call(this.attrs, nom) ? this.attrs[nom] : null;
  }

  get href() {
    /* Le lecteur lit `a.href`, qui dans un navigateur est absolu. Les gabarits
     * n'ont pas de base: on rend l'attribut tel quel, ce qui suffit puisque
     * seule la presence du marqueur compte. */
    return this.attrs["href"] || "";
  }

  descendants() {
    const sortie = [];
    for (const enfant of this.enfants) {
      if (enfant.tagName !== "#TEXTE") sortie.push(enfant);
      sortie.push(...enfant.descendants());
    }
    return sortie;
  }

  /* Selecteurs acceptes, et rien d'autre: `tag`, `.classe`, `tag.classe`,
   * `[attr]`, `a[href]`. Un selecteur non reconnu jette, plutot que de rendre
   * une liste vide qui ferait passer un test pour bon. */
  querySelectorAll(selecteur) {
    const filtre = compiler(selecteur);
    return this.descendants().filter(filtre);
  }

  querySelector(selecteur) {
    return this.querySelectorAll(selecteur)[0] || null;
  }
}

function compiler(selecteur) {
  const s = selecteur.trim();
  let m = s.match(/^([a-z]+)?\.([\w-]+)$/i);
  if (m) {
    const [, tag, classe] = m;
    return (n) =>
      (!tag || n.nomBalise === tag.toLowerCase()) && n.classList.contains(classe);
  }
  m = s.match(/^([a-z]*)\[([\w-]+)\]$/i);
  if (m) {
    const [, tag, attr] = m;
    return (n) =>
      (!tag || n.nomBalise === tag.toLowerCase()) && n.getAttribute(attr) !== null;
  }
  if (/^[a-z]+$/i.test(s)) return (n) => n.nomBalise === s.toLowerCase();
  throw new Error(
    `mini-dom: selecteur non gere ${JSON.stringify(selecteur)}. ` +
      "Le refus est deliberé: rendre une liste vide ferait passer un test pour bon."
  );
}

const BALISE = /<(\/?)([a-zA-Z][\w-]*)((?:\s+[\w-]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>/g;
const ATTR = /([\w-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;

export function analyser(html) {
  const racine = new Noeud("#racine");
  const pile = [racine];
  let position = 0;
  let m;
  BALISE.lastIndex = 0;
  while ((m = BALISE.exec(html)) !== null) {
    const texte = html.slice(position, m.index);
    if (texte.trim()) {
      const noeud = new Noeud("#texte");
      noeud.texteBrut = texte;
      pile[pile.length - 1].enfants.push(noeud);
    }
    position = BALISE.lastIndex;
    const [, fermante, nom, attributs, autoFermante] = m;
    if (fermante) {
      for (let i = pile.length - 1; i > 0; i--) {
        if (pile[i].nomBalise === nom.toLowerCase()) {
          pile.length = i;
          break;
        }
      }
      continue;
    }
    const attrs = {};
    let a;
    ATTR.lastIndex = 0;
    while ((a = ATTR.exec(attributs || "")) !== null) {
      attrs[a[1].toLowerCase()] = a[2] ?? a[3] ?? a[4] ?? "";
    }
    const noeud = new Noeud(nom, attrs);
    noeud.parent = pile[pile.length - 1];
    pile[pile.length - 1].enfants.push(noeud);
    if (!autoFermante && !AUTO_FERMANTS.has(nom.toLowerCase())) pile.push(noeud);
  }
  return racine;
}

/* Le `document` que voit le lecteur. `location.pathname` decide s'il lit un
 * index de documents ou un etat de depenses, donc il fait partie du gabarit. */
/* Un noeud fabrique a la main, par opposition a un noeud analyse depuis du
 * HTML. Il porte le minimum dont le bandeau et le panneau ont besoin: de quoi
 * se construire, s'attacher, et se relire.
 *
 * Ajoute le 2026-09-07. Avant, `fabriquerDocument` ne rendait ni `body`, ni
 * `createElement`, ni `attachShadow` - de sorte que le bandeau de `lecteur.js`
 * sortait par sa propre garde a chaque execution de test. Le code du bandeau
 * n'avait donc **jamais** ete exerce, et son echec eventuel etait masque par
 * la garde meme qui devait le proteger en production. */
class NoeudFabrique extends Noeud {
  constructor(nom) {
    super(nom, {});
    this._texte = "";
    this._classe = "";
    this.id = "";
    this.dataset = {};
    this.hidden = false;
    this.style = {};
    this.shadow = null;
    this._ecoutes = {};
  }

  /* `Noeud` derive `textContent` et `className` du HTML analyse, donc en
   * lecture seule. Un noeud fabrique les porte lui-meme. */
  get textContent() {
    return this._texte || this.enfants.map((e) => e.textContent).join("");
  }

  set textContent(valeur) {
    this._texte = String(valeur);
    this.enfants = [];
  }

  get className() {
    return this._classe;
  }

  set className(valeur) {
    this._classe = String(valeur);
    this.attrs.class = this._classe;
  }

  appendChild(enfant) {
    enfant.parent = this;
    this.enfants.push(enfant);
    return enfant;
  }

  append(...enfants) {
    for (const e of enfants) this.appendChild(e);
  }

  remove() {
    if (!this.parent) return;
    const i = this.parent.enfants.indexOf(this);
    if (i >= 0) this.parent.enfants.splice(i, 1);
  }

  setAttribute(nom, valeur) {
    this.attrs[nom.toLowerCase()] = String(valeur);
  }

  addEventListener(nom, fn) {
    (this._ecoutes[nom] = this._ecoutes[nom] || []).push(fn);
  }

  attachShadow() {
    this.shadow = new NoeudFabrique("#shadow");
    this.shadow.parent = this;
    return this.shadow;
  }

  set innerHTML(valeur) {
    /* Le seul usage reel est la remise a zero d'une zone. Accepter du HTML
     * arbitraire ici donnerait au harnais un pouvoir que la page n'a pas. */
    if (String(valeur) !== "") {
      throw new Error("mini-dom: innerHTML n'accepte que la chaine vide");
    }
    this.enfants = [];
  }

  /* Le texte de tout le sous-arbre, ombre comprise. C'est ce qu'un lecteur
   * humain verrait. */
  get texteProfond() {
    let sortie = this._texte || "";
    const enfants = this.shadow ? [this.shadow, ...this.enfants] : this.enfants;
    for (const e of enfants) {
      sortie += " " + (e.texteProfond !== undefined ? e.texteProfond : e.textContent);
    }
    return sortie.trim();
  }
}

export function fabriquerDocument(html) {
  const racine = analyser(html);
  const body = new NoeudFabrique("body");
  const parIdentifiant = new Map();
  const doc = {
    querySelectorAll: (s) => racine.querySelectorAll(s),
    querySelector: (s) => racine.querySelector(s),
    racine,
    body,
    createElement: (nom) => new NoeudFabrique(nom),
    createTextNode: (t) => {
      const n = new NoeudFabrique("#text");
      n.textContent = t;
      return n;
    },
    getElementById: (id) => {
      const chercher = (n) => {
        if (n.id === id) return n;
        for (const e of n.enfants || []) {
          const trouve = chercher(e);
          if (trouve) return trouve;
        }
        return null;
      };
      return parIdentifiant.get(id) || chercher(body);
    },
  };
  return doc;
}

export { NoeudFabrique };
