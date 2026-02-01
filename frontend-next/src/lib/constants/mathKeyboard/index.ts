// Matematik Klavyesi - Ana Export Dosyası
// Tüm kategorileri birleştirir ve export eder

export * from './types';

// Matematik kategorileri
import { basicSymbols } from './basic';
import { superscriptSymbols } from './superscript';
import { calculusSymbols } from './calculus';
import { linearAlgebraSymbols } from './linearAlgebra';
import { probabilitySymbols } from './probability';
import { statisticsSymbols } from './statistics';
import { setsSymbols } from './sets';
import { greekSymbols } from './greek';
import { trigonometrySymbols } from './trigonometry';
import { arrowsSymbols } from './arrows';
import { geometrySymbols } from './geometry';

// Yeni eklenen kategoriler
import { fractionsSymbols } from './fractions';
import { romanNumeralsSymbols } from './romanNumerals';
import { physicsSymbols } from './physics';
import { currencySymbols } from './currency';
import { logicSymbols } from './logic';
import { numberTheorySymbols } from './numberTheory';
import { bracketsSymbols } from './brackets';
import { miscellaneousSymbols } from './miscellaneous';

// Normal klavye kategorileri
import { 
  turkishSymbols, 
  accentedSymbols, 
  punctuationSymbols, 
  emojiSymbols, 
  mathOperatorsSymbols,
  NORMAL_KEYBOARD_CATEGORIES 
} from './normalKeyboard';

import type { MathKeyboardCategory } from './types';

// Matematik klavyesi tüm kategorileri
export const MATH_KEYBOARD_CATEGORIES: MathKeyboardCategory[] = [
  basicSymbols,
  superscriptSymbols,
  greekSymbols,
  calculusSymbols,
  linearAlgebraSymbols,
  probabilitySymbols,
  statisticsSymbols,
  trigonometrySymbols,
  setsSymbols,
  logicSymbols,
  numberTheorySymbols,
  geometrySymbols,
  arrowsSymbols,
  bracketsSymbols,
  fractionsSymbols,
  romanNumeralsSymbols,
  physicsSymbols,
  currencySymbols,
  miscellaneousSymbols,
];

// Normal klavye kategorileri
export { NORMAL_KEYBOARD_CATEGORIES };

// Bireysel export'lar (gerekirse)
export {
  basicSymbols,
  superscriptSymbols,
  calculusSymbols,
  linearAlgebraSymbols,
  probabilitySymbols,
  statisticsSymbols,
  setsSymbols,
  greekSymbols,
  trigonometrySymbols,
  arrowsSymbols,
  geometrySymbols,
  fractionsSymbols,
  romanNumeralsSymbols,
  physicsSymbols,
  currencySymbols,
  logicSymbols,
  numberTheorySymbols,
  bracketsSymbols,
  miscellaneousSymbols,
  turkishSymbols,
  accentedSymbols,
  punctuationSymbols,
  emojiSymbols,
  mathOperatorsSymbols,
};

// Toplam sembol sayısını hesapla
export const getTotalSymbolCount = (): { math: number; normal: number; total: number } => {
  const mathCount = MATH_KEYBOARD_CATEGORIES.reduce((acc, cat) => acc + cat.symbols.length, 0);
  const normalCount = NORMAL_KEYBOARD_CATEGORIES.reduce((acc, cat) => acc + cat.symbols.length, 0);
  return {
    math: mathCount,
    normal: normalCount,
    total: mathCount + normalCount,
  };
};

// Kategori sayısını al
export const getCategoryCount = (): { math: number; normal: number; total: number } => ({
  math: MATH_KEYBOARD_CATEGORIES.length,
  normal: NORMAL_KEYBOARD_CATEGORIES.length,
  total: MATH_KEYBOARD_CATEGORIES.length + NORMAL_KEYBOARD_CATEGORIES.length,
});
