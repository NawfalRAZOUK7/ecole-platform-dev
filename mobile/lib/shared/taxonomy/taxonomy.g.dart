// GENERATED FILE — DO NOT EDIT BY HAND.
// Source of truth: design-tokens/taxonomy.json (dumped from the backend enums).
// Regenerate: node scripts/generate-taxonomy.mjs
//
// Mirrors backend/app/models/taxonomy.py so every level/subject input in the
// mobile app draws from the same set the backend accepts.

/// Curriculum vocabulary, generated from the backend taxonomy.
class Taxonomy {
  Taxonomy._();

  static const String subjectOther = 'other';

  static const List<String> schoolCycles = [
    'prescolaire',
    'primaire',
    'college',
    'lycee',
  ];

  static const List<String> microSchoolTypes = [
    'rawd',
    'msid',
    'non_formel',
    'general',
  ];

  static const List<String> levelBands = [
    'PS',
    'MS',
    'GS',
    '1AEP',
    '2AEP',
    '3AEP',
    '4AEP',
    '5AEP',
    '6AEP',
    '1AC',
    '2AC',
    '3AC',
    'TC',
    '1BAC',
    '2BAC',
  ];

  static const List<String> subjects = [
    'arabic',
    'french',
    'english',
    'amazigh',
    'math',
    'activite_scientifique',
    'svt',
    'physique_chimie',
    'histoire_geo',
    'civic',
    'philosophy',
    'islamic',
    'quranic',
    'art',
    'music',
    'sport',
    'informatique',
    'technology',
    'economics',
    'accounting',
    'arabic_letters',
    'literacy',
    'vocabulary',
    'pedagogy',
    'other',
  ];

  static const List<String> difficultyLevels = [
    'EASY',
    'MEDIUM',
    'HARD',
  ];

  static const List<String> languages = [
    'fr',
    'ar',
    'en',
  ];

  static const List<String> currencies = [
    'MAD',
    'EUR',
    'USD',
  ];

  /// Subject code -> {fr, ar, en} display titles.
  static const Map<String, Map<String, String>> subjectTitles = {
    'arabic': {'fr': 'Langue arabe', 'ar': 'اللغة العربية', 'en': 'Arabic'},
    'french': {'fr': 'Langue française', 'ar': 'اللغة الفرنسية', 'en': 'French'},
    'english': {'fr': 'Langue anglaise', 'ar': 'اللغة الإنجليزية', 'en': 'English'},
    'amazigh': {'fr': 'Langue amazighe', 'ar': 'اللغة الأمازيغية', 'en': 'Amazigh'},
    'arabic_letters': {'fr': 'Lettres arabes', 'ar': 'الحروف العربية', 'en': 'Arabic letters'},
    'math': {'fr': 'Mathématiques', 'ar': 'الرياضيات', 'en': 'Mathematics'},
    'activite_scientifique': {'fr': 'Activité scientifique', 'ar': 'النشاط العلمي', 'en': 'Scientific activity'},
    'svt': {'fr': 'Sciences de la vie et de la Terre', 'ar': 'علوم الحياة والأرض', 'en': 'Life & earth sciences'},
    'physique_chimie': {'fr': 'Physique-Chimie', 'ar': 'الفيزياء والكيمياء', 'en': 'Physics-Chemistry'},
    'histoire_geo': {'fr': 'Éducation sociale (histoire-géographie)', 'ar': 'الاجتماعيات', 'en': 'Social studies'},
    'civic': {'fr': 'Éducation à la citoyenneté', 'ar': 'التربية على المواطنة', 'en': 'Civic education'},
    'philosophy': {'fr': 'Philosophie', 'ar': 'الفلسفة', 'en': 'Philosophy'},
    'islamic': {'fr': 'Éducation islamique', 'ar': 'التربية الإسلامية', 'en': 'Islamic education'},
    'quranic': {'fr': 'Coran (mémorisation)', 'ar': 'القرآن الكريم (حفظ وتجويد)', 'en': 'Quran (memorisation)'},
    'art': {'fr': 'Éducation artistique', 'ar': 'التربية الفنية', 'en': 'Arts'},
    'music': {'fr': 'Éducation musicale', 'ar': 'التربية الموسيقية', 'en': 'Music'},
    'sport': {'fr': 'Éducation physique', 'ar': 'التربية البدنية', 'en': 'Physical education'},
    'informatique': {'fr': 'Informatique (TICE)', 'ar': 'المعلوميات', 'en': 'Computing'},
    'technology': {'fr': 'Technologie', 'ar': 'التكنولوجيا', 'en': 'Technology'},
    'economics': {'fr': 'Économie', 'ar': 'الاقتصاد', 'en': 'Economics'},
    'accounting': {'fr': 'Comptabilité', 'ar': 'المحاسبة', 'en': 'Accounting'},
    'literacy': {'fr': 'Pré-lecture', 'ar': 'القراءة الأولية', 'en': 'Literacy'},
    'vocabulary': {'fr': 'Vocabulaire', 'ar': 'المفردات', 'en': 'Vocabulary'},
    'pedagogy': {'fr': 'Pédagogie', 'ar': 'البيداغوجيا', 'en': 'Pedagogy'},
  };

  /// School cycle -> allowed subject codes.
  static const Map<String, List<String>> cycleSubjects = {
    'prescolaire': ['arabic', 'french', 'math', 'activite_scientifique', 'islamic', 'art', 'music', 'sport', 'arabic_letters', 'literacy', 'vocabulary'],
    'primaire': ['arabic', 'french', 'english', 'amazigh', 'math', 'activite_scientifique', 'islamic', 'histoire_geo', 'civic', 'art', 'music', 'sport', 'informatique', 'arabic_letters', 'literacy', 'vocabulary'],
    'college': ['arabic', 'french', 'english', 'amazigh', 'math', 'svt', 'physique_chimie', 'histoire_geo', 'civic', 'islamic', 'art', 'sport', 'informatique', 'technology'],
    'lycee': ['arabic', 'french', 'english', 'math', 'svt', 'physique_chimie', 'histoire_geo', 'civic', 'philosophy', 'islamic', 'sport', 'informatique', 'economics', 'accounting', 'technology'],
  };
}
