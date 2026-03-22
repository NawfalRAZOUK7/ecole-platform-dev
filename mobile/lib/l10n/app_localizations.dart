/// Lightweight i18n helper for Phase 10C screens.
///
/// Uses a simple Map-based approach consistent with the existing mobile app
/// architecture (no flutter_localizations dependency needed).
/// Supports fr (default), ar, en.
/// The API client's Accept-Language header is set via ApiClient.setLocale().
///
/// Usage:
///   final t = AppLocalizations.of(context);
///   Text(t['contentLibrary.title']!)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Current locale provider.
final localeProvider = StateProvider<String>((ref) => 'fr');

/// Translation strings by locale.
const Map<String, Map<String, String>> _translations = {
  'fr': {
    // ── Nav ──
    'nav.contentLibrary': 'Bibliothèque',
    'nav.studentContent': 'Contenu',
    'nav.studentQuiz': 'Quiz',
    'nav.results': 'Résultats',

    // ── Teacher Content Library ──
    'contentLibrary.title': 'Bibliothèque de contenu',
    'contentLibrary.browse': 'Parcourir',
    'contentLibrary.upload': 'Téléverser',
    'contentLibrary.submissions': 'Soumissions',
    'contentLibrary.searchHint': 'Rechercher du contenu...',
    'contentLibrary.filterAll': 'Tous',
    'contentLibrary.filterPlatform': 'Plateforme',
    'contentLibrary.filterSchool': 'École',
    'contentLibrary.assignToClass': 'Assigner à une classe',
    'contentLibrary.submitForReview': 'Soumettre pour révision',
    'contentLibrary.noContent': 'Aucun contenu disponible',
    'contentLibrary.uploadTitle': 'Titre',
    'contentLibrary.uploadDescription': 'Description',
    'contentLibrary.uploadType': 'Type de contenu',
    'contentLibrary.uploadLanguage': 'Langue',
    'contentLibrary.uploadFile': 'Fichier',
    'contentLibrary.uploadBtn': 'Téléverser',
    'contentLibrary.uploadSuccess': 'Contenu téléversé avec succès',
    'contentLibrary.noSubmissions': 'Aucune soumission',
    'contentLibrary.assigned': 'Contenu assigné à',
    'contentLibrary.submitted': 'Soumis pour révision',
    'contentLibrary.statusPending': 'En attente',
    'contentLibrary.statusApproved': 'Approuvé',
    'contentLibrary.statusRejected': 'Rejeté',
    'contentLibrary.statusPromoted': 'Promu',

    // ── Student Content ──
    'studentContent.title': 'Mon contenu',
    'studentContent.noContent': 'Aucun contenu assigné',
    'studentContent.markComplete': 'Terminé',
    'studentContent.markedComplete': 'Marqué comme terminé',
    'studentContent.playVideo': 'Lire la vidéo',
    'studentContent.listen': 'Écouter',
    'studentContent.openDoc': 'Ouvrir le document',
    'studentContent.open': 'Ouvrir',
    'studentContent.progressNew': 'Nouveau',
    'studentContent.progressStarted': 'En cours',
    'studentContent.progressCompleted': 'Terminé',

    // ── Student Quiz ──
    'quiz.title': 'Quiz',
    'quiz.noQuizzes': 'Aucun quiz disponible',
    'quiz.start': 'Commencer',
    'quiz.submit': 'Soumettre',
    'quiz.submitting': 'Envoi...',
    'quiz.previous': 'Précédent',
    'quiz.next': 'Suivant',
    'quiz.exitTitle': 'Quitter le quiz ?',
    'quiz.exitMsg': 'Vos réponses seront perdues si vous quittez maintenant.',
    'quiz.cancel': 'Annuler',
    'quiz.exit': 'Quitter',
    'quiz.results': 'Résultats',
    'quiz.bravo': 'Bravo !',
    'quiz.keepTrying': 'Continuez vos efforts !',
    'quiz.details': 'Détails par question',
    'quiz.yourAnswer': 'Votre réponse',
    'quiz.correctAnswer': 'Réponse correcte',
    'quiz.backToList': 'Retour aux quiz',
    'quiz.fillInHint': 'Tapez votre réponse ici...',
    'quiz.fillInLabel': 'Votre réponse',
    'quiz.trueLabel': 'Vrai',
    'quiz.falseLabel': 'Faux',
    'quiz.dragDropHint': 'Faites glisser les éléments vers les zones :',
    'quiz.matchingHint': 'Associez chaque élément de gauche avec celui de droite :',
    'quiz.selectHint': 'Sélectionner...',
    'quiz.easy': 'Facile',
    'quiz.medium': 'Moyen',
    'quiz.hard': 'Difficile',
    'quiz.questions': 'questions',
    'quiz.pts': 'pts',
    'quiz.min': 'min',

    // ── Results ──
    'results.title': 'Résultats',
    'results.tabAssignments': 'Devoirs',
    'results.tabQuizzes': 'Quiz',
    'results.noResults': 'Aucun résultat disponible',
    'results.noQuizResults': 'Aucun résultat de quiz',
    'results.attempt': 'Tentative',
    'results.retry': 'Réessayer',

    // ── Submission PDF ──
    'submission.pdfExercise': 'Exercice à imprimer',
    'submission.pdfInstructions': '1. Téléchargez et imprimez le PDF\n2. Résolvez l\'exercice sur papier\n3. Prenez en photo votre solution',
    'submission.downloadPdf': 'Télécharger le PDF',
    'submission.downloading': 'Téléchargement...',

    // ── Profile ──
    'profile.rewardPoints': 'Points de récompense',

    // ── Common ──
    'common.error': 'Erreur',
    'common.retry': 'Réessayer',
    'common.loading': 'Chargement...',
  },

  'ar': {
    // ── Nav ──
    'nav.contentLibrary': 'المكتبة',
    'nav.studentContent': 'المحتوى',
    'nav.studentQuiz': 'اختبارات',
    'nav.results': 'النتائج',

    // ── Teacher Content Library ──
    'contentLibrary.title': 'مكتبة المحتوى',
    'contentLibrary.browse': 'تصفح',
    'contentLibrary.upload': 'رفع',
    'contentLibrary.submissions': 'طلبات المراجعة',
    'contentLibrary.searchHint': 'بحث عن محتوى...',
    'contentLibrary.filterAll': 'الكل',
    'contentLibrary.filterPlatform': 'المنصة',
    'contentLibrary.filterSchool': 'المدرسة',
    'contentLibrary.assignToClass': 'تعيين للفصل',
    'contentLibrary.submitForReview': 'تقديم للمراجعة',
    'contentLibrary.noContent': 'لا يوجد محتوى متاح',
    'contentLibrary.uploadTitle': 'العنوان',
    'contentLibrary.uploadDescription': 'الوصف',
    'contentLibrary.uploadType': 'نوع المحتوى',
    'contentLibrary.uploadLanguage': 'اللغة',
    'contentLibrary.uploadFile': 'ملف',
    'contentLibrary.uploadBtn': 'رفع',
    'contentLibrary.uploadSuccess': 'تم رفع المحتوى بنجاح',
    'contentLibrary.noSubmissions': 'لا توجد طلبات مراجعة',
    'contentLibrary.assigned': 'تم تعيين المحتوى لـ',
    'contentLibrary.submitted': 'تم التقديم للمراجعة',
    'contentLibrary.statusPending': 'قيد الانتظار',
    'contentLibrary.statusApproved': 'موافق عليه',
    'contentLibrary.statusRejected': 'مرفوض',
    'contentLibrary.statusPromoted': 'تمت ترقيته',

    // ── Student Content ──
    'studentContent.title': 'محتواي',
    'studentContent.noContent': 'لا يوجد محتوى معين',
    'studentContent.markComplete': 'مكتمل',
    'studentContent.markedComplete': 'تم وضع علامة مكتمل',
    'studentContent.playVideo': 'تشغيل الفيديو',
    'studentContent.listen': 'استماع',
    'studentContent.openDoc': 'فتح المستند',
    'studentContent.open': 'فتح',
    'studentContent.progressNew': 'جديد',
    'studentContent.progressStarted': 'قيد التقدم',
    'studentContent.progressCompleted': 'مكتمل',

    // ── Student Quiz ──
    'quiz.title': 'اختبارات',
    'quiz.noQuizzes': 'لا توجد اختبارات متاحة',
    'quiz.start': 'ابدأ',
    'quiz.submit': 'إرسال',
    'quiz.submitting': 'جاري الإرسال...',
    'quiz.previous': 'السابق',
    'quiz.next': 'التالي',
    'quiz.exitTitle': 'مغادرة الاختبار؟',
    'quiz.exitMsg': 'ستفقد إجاباتك إذا غادرت الآن.',
    'quiz.cancel': 'إلغاء',
    'quiz.exit': 'مغادرة',
    'quiz.results': 'النتائج',
    'quiz.bravo': 'أحسنت!',
    'quiz.keepTrying': 'واصل المحاولة!',
    'quiz.details': 'تفاصيل كل سؤال',
    'quiz.yourAnswer': 'إجابتك',
    'quiz.correctAnswer': 'الإجابة الصحيحة',
    'quiz.backToList': 'العودة للاختبارات',
    'quiz.fillInHint': 'اكتب إجابتك هنا...',
    'quiz.fillInLabel': 'إجابتك',
    'quiz.trueLabel': 'صحيح',
    'quiz.falseLabel': 'خطأ',
    'quiz.dragDropHint': 'اسحب العناصر إلى المناطق:',
    'quiz.matchingHint': 'طابق كل عنصر من اليسار مع اليمين:',
    'quiz.selectHint': 'اختر...',
    'quiz.easy': 'سهل',
    'quiz.medium': 'متوسط',
    'quiz.hard': 'صعب',
    'quiz.questions': 'أسئلة',
    'quiz.pts': 'نقاط',
    'quiz.min': 'دقيقة',

    // ── Results ──
    'results.title': 'النتائج',
    'results.tabAssignments': 'الواجبات',
    'results.tabQuizzes': 'الاختبارات',
    'results.noResults': 'لا توجد نتائج',
    'results.noQuizResults': 'لا توجد نتائج اختبارات',
    'results.attempt': 'المحاولة',
    'results.retry': 'إعادة المحاولة',

    // ── Submission PDF ──
    'submission.pdfExercise': 'تمرين للطباعة',
    'submission.pdfInstructions': '1. حمّل واطبع ملف PDF\n2. حل التمرين على الورق\n3. التقط صورة لحلك',
    'submission.downloadPdf': 'تحميل PDF',
    'submission.downloading': 'جاري التحميل...',

    // ── Profile ──
    'profile.rewardPoints': 'نقاط المكافأة',

    // ── Common ──
    'common.error': 'خطأ',
    'common.retry': 'إعادة المحاولة',
    'common.loading': 'جاري التحميل...',
  },

  'en': {
    // ── Nav ──
    'nav.contentLibrary': 'Library',
    'nav.studentContent': 'Content',
    'nav.studentQuiz': 'Quizzes',
    'nav.results': 'Results',

    // ── Teacher Content Library ──
    'contentLibrary.title': 'Content Library',
    'contentLibrary.browse': 'Browse',
    'contentLibrary.upload': 'Upload',
    'contentLibrary.submissions': 'Submissions',
    'contentLibrary.searchHint': 'Search content...',
    'contentLibrary.filterAll': 'All',
    'contentLibrary.filterPlatform': 'Platform',
    'contentLibrary.filterSchool': 'School',
    'contentLibrary.assignToClass': 'Assign to class',
    'contentLibrary.submitForReview': 'Submit for review',
    'contentLibrary.noContent': 'No content available',
    'contentLibrary.uploadTitle': 'Title',
    'contentLibrary.uploadDescription': 'Description',
    'contentLibrary.uploadType': 'Content type',
    'contentLibrary.uploadLanguage': 'Language',
    'contentLibrary.uploadFile': 'File',
    'contentLibrary.uploadBtn': 'Upload',
    'contentLibrary.uploadSuccess': 'Content uploaded successfully',
    'contentLibrary.noSubmissions': 'No submissions',
    'contentLibrary.assigned': 'Content assigned to',
    'contentLibrary.submitted': 'Submitted for review',
    'contentLibrary.statusPending': 'Pending',
    'contentLibrary.statusApproved': 'Approved',
    'contentLibrary.statusRejected': 'Rejected',
    'contentLibrary.statusPromoted': 'Promoted',

    // ── Student Content ──
    'studentContent.title': 'My Content',
    'studentContent.noContent': 'No assigned content',
    'studentContent.markComplete': 'Complete',
    'studentContent.markedComplete': 'Marked as complete',
    'studentContent.playVideo': 'Play video',
    'studentContent.listen': 'Listen',
    'studentContent.openDoc': 'Open document',
    'studentContent.open': 'Open',
    'studentContent.progressNew': 'New',
    'studentContent.progressStarted': 'In progress',
    'studentContent.progressCompleted': 'Completed',

    // ── Student Quiz ──
    'quiz.title': 'Quizzes',
    'quiz.noQuizzes': 'No quizzes available',
    'quiz.start': 'Start',
    'quiz.submit': 'Submit',
    'quiz.submitting': 'Submitting...',
    'quiz.previous': 'Previous',
    'quiz.next': 'Next',
    'quiz.exitTitle': 'Leave quiz?',
    'quiz.exitMsg': 'Your answers will be lost if you leave now.',
    'quiz.cancel': 'Cancel',
    'quiz.exit': 'Leave',
    'quiz.results': 'Results',
    'quiz.bravo': 'Well done!',
    'quiz.keepTrying': 'Keep trying!',
    'quiz.details': 'Question details',
    'quiz.yourAnswer': 'Your answer',
    'quiz.correctAnswer': 'Correct answer',
    'quiz.backToList': 'Back to quizzes',
    'quiz.fillInHint': 'Type your answer here...',
    'quiz.fillInLabel': 'Your answer',
    'quiz.trueLabel': 'True',
    'quiz.falseLabel': 'False',
    'quiz.dragDropHint': 'Drag items to the zones:',
    'quiz.matchingHint': 'Match each item on the left with one on the right:',
    'quiz.selectHint': 'Select...',
    'quiz.easy': 'Easy',
    'quiz.medium': 'Medium',
    'quiz.hard': 'Hard',
    'quiz.questions': 'questions',
    'quiz.pts': 'pts',
    'quiz.min': 'min',

    // ── Results ──
    'results.title': 'Results',
    'results.tabAssignments': 'Assignments',
    'results.tabQuizzes': 'Quizzes',
    'results.noResults': 'No results available',
    'results.noQuizResults': 'No quiz results',
    'results.attempt': 'Attempt',
    'results.retry': 'Retry',

    // ── Submission PDF ──
    'submission.pdfExercise': 'Printable exercise',
    'submission.pdfInstructions': '1. Download and print the PDF\n2. Solve the exercise on paper\n3. Take a photo of your solution',
    'submission.downloadPdf': 'Download PDF',
    'submission.downloading': 'Downloading...',

    // ── Profile ──
    'profile.rewardPoints': 'Reward Points',

    // ── Common ──
    'common.error': 'Error',
    'common.retry': 'Retry',
    'common.loading': 'Loading...',
  },
};

/// Get translations for a locale. Falls back to French.
Map<String, String> getTranslations(String locale) {
  return _translations[locale] ?? _translations['fr']!;
}

/// Simple i18n accessor — call with ref.watch(localeProvider).
class AppLocalizations {
  final String locale;

  const AppLocalizations(this.locale);

  /// Get a translation by key. Falls back to French, then returns key.
  String t(String key) {
    return _translations[locale]?[key] ??
        _translations['fr']?[key] ??
        key;
  }

  /// Convenience: create from Riverpod ref.
  static AppLocalizations of(WidgetRef ref) {
    final locale = ref.watch(localeProvider);
    return AppLocalizations(locale);
  }
}
