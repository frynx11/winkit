# -*- coding: utf-8 -*-
"""WinKit 2.0 - Windows maintenance, diagnostics and productivity hub.

Requires Windows 10/11, Python 3.10+, PySide6 and psutil.
The app does not silently disable security controls or perform bulk destructive changes.
"""
from __future__ import annotations

import ctypes
import hashlib
import html
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import psutil
except ImportError:  # App can still open; live metrics will show an installation hint.
    psutil = None

from PySide6.QtCore import (
    QEasingCurve, QObject, Property, QPropertyAnimation, QRunnable, QThreadPool,
    QTimer, Qt, QUrl, Signal, QSize
)
from PySide6.QtGui import QAction, QDesktopServices, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QVBoxLayout, QWidget, QInputDialog
)

APP_NAME = "WinKit"
APP_VERSION = "2.0.0"
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home() / ".config"))) / APP_NAME
SETTINGS_PATH = APP_DIR / "settings.json"
BACKUP_PATH = APP_DIR / "registry_backups.json"
LOG_PATH = APP_DIR / "activity.json"

# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------
TEXTS: dict[str, dict[str, str]] = {
    "ar": {
        "app_subtitle": "مركز التحكم والصيانة والإنتاجية لويندوز",
        "dashboard": "لوحة التحكم", "tools": "الأدوات السريعة", "cleanup": "التنظيف",
        "repair": "الإصلاح الذكي", "network": "الشبكة", "performance": "الأداء والألعاب",
        "hardware": "مراقبة الجهاز", "software": "مركز البرامج", "disk": "تحليل القرص",
        "report": "تقرير النظام", "favorites": "المفضلة", "activity": "سجل النشاط",
        "settings": "الإعدادات", "search": "ابحث عن أداة أو أمر...", "language": "اللغة",
        "theme": "الثيم", "welcome": "كل أدوات ويندوز في مكان واحد",
        "welcome_sub": "افحص جهازك، أصلح المشاكل، وأدر البرامج من واجهة واحدة.",
        "cpu": "المعالج", "ram": "الذاكرة", "disk_usage": "القرص", "uptime": "مدة التشغيل",
        "quick_actions": "إجراءات سريعة", "recent": "آخر الأنشطة", "all_tools": "كل الأدوات",
        "run": "تشغيل", "copy": "نسخ الأمر", "favorite": "إضافة للمفضلة",
        "unfavorite": "إزالة من المفضلة", "safe": "آمن", "medium": "متوسط",
        "high": "مرتفع", "reversible": "قابل للاسترجاع", "no_results": "لا توجد نتائج مطابقة.",
        "ready": "جاهز", "working": "جارٍ التنفيذ...", "done": "اكتمل",
        "error": "حدث خطأ", "confirm": "تأكيد العملية", "cancel": "إلغاء",
        "close": "إغلاق", "save": "حفظ", "refresh": "تحديث", "open": "فتح",
        "copy_done": "تم نسخ الأمر إلى الحافظة.", "windows_only": "هذه الوظيفة متاحة على Windows فقط.",
        "dashboard_hint": "ملخص سريع لحالة الجهاز والأدوات الأكثر استخدامًا.",
        "fix_title": "مركز الإصلاح الذكي", "fix_desc": "شغّل فحوصات تشخيصية أولًا، ثم اختر الإصلاح المناسب.",
        "network_test": "تشخيص الاتصال", "network_test_desc": "يفحص البوابة المحلية وDNS والاتصال الخارجي.",
        "scan_running": "جارٍ الفحص...", "scan_complete": "انتهى الفحص.",
        "software_title": "مركز البرامج", "software_desc": "اعرض البرامج المثبتة والتحديثات المتاحة عبر WinGet.",
        "installed_apps": "البرامج المثبتة", "check_updates": "فحص التحديثات",
        "update_all": "تحديث البرامج المتاحة", "export_apps": "تصدير قائمة البرامج", "import_apps": "استعادة قائمة البرامج",
        "winget_missing": "WinGet غير موجود. ثبّت App Installer من Microsoft Store ثم أعد المحاولة.",
        "update_warning": "سيتم فتح نافذة أوامر تعرض تحديث البرامج المتاحة. راجع قائمة الحزم قبل الموافقة على أي مثبت. هل تريد المتابعة؟",
        "report_title": "تقرير النظام", "report_desc": "أنشئ تقريرًا محليًا عن الجهاز واحفظه بصيغة HTML.",
        "generate_report": "إنشاء التقرير", "report_saved": "تم حفظ التقرير.",
        "disk_title": "محلل مساحة القرص", "disk_desc": "اختر مجلدًا لعرض أكبر الملفات وأنواع الملفات. لا يتم حذف أي شيء.",
        "choose_folder": "اختيار مجلد", "scan_folder": "تحليل المجلد", "scanning": "جارٍ تحليل الملفات...",
        "disk_empty": "اختر مجلدًا لبدء التحليل.", "hash_title": "فاحص SHA-256", "hash_desc": "احسب بصمة ملف لمقارنة سلامته.",
        "choose_file": "اختيار ملف", "hash_result": "بصمة SHA-256:",
        "performance_title": "استوديو الأداء", "performance_desc": "بريستات محسوبة مع نسخ احتياطية وإمكانية استعادة التغييرات.",
        "low_end": "بريست الأجهزة الضعيفة", "low_end_desc": "يقلل بعض مؤثرات الواجهة للحساب الحالي فقط. لا يضمن زيادة FPS.",
        "restore": "استعادة إعدادات WinKit السابقة", "gaming": "إعدادات الألعاب",
        "battery": "إعدادات توفير الطاقة", "startup": "إدارة تطبيقات بدء التشغيل",
        "theme_note": "الثيم هنا يغيّر واجهة WinKit فقط، وليس ألوان Windows.",
        "appearance_note": "تغيير ألوان Windows إجراء منفصل موجود ضمن الأدوات.",
        "activity_empty": "لم يتم تنفيذ أي أدوات بعد.", "settings_title": "تخصيص WinKit",
        "settings_desc": "اختر لغة الواجهة والثيم المفضل. يتم حفظ اختياراتك محليًا.",
        "theme_dark": "Dark Fluent", "theme_light": "Clean Light", "theme_midnight": "Midnight",
        "theme_graphite": "Graphite", "language_ar": "العربية", "language_en": "English",
        "language_fr": "Français", "restart_hint": "يتم تطبيق اللغة مباشرة على الواجهة.",
        "command": "الأمر", "description": "الوصف", "risk": "مستوى التأثير",
        "admin_note": "قد يطلب Windows صلاحية المسؤول عبر نافذة UAC.",
        "danger_note": "اقرأ التأثير جيدًا قبل المتابعة. بعض العمليات لا يمكن التراجع عنها.",
        "no_backup": "لا توجد نسخة احتياطية محفوظة لهذه الإعدادات.",
        "report_open": "فتح التقرير", "processes": "أكثر العمليات استهلاكًا للذاكرة",
        "gpu_unavailable": "قراءة GPU غير متاحة عبر أدوات النظام العامة على هذا الجهاز.",
        "metrics_unavailable": "ثبّت المتطلبات من requirements.txt لعرض مراقبة الجهاز.",
        "scan_limit": "تم الوصول إلى حد الملفات الآمن للتحليل.",
        "folder_error": "تعذر فحص بعض الملفات بسبب الصلاحيات أو استخدامها.",
        "quick_search_tip": "اختصار البحث داخل WinKit: Ctrl + K",
        "software_note": "قد يطلب WinGet مراجعة اتفاقيات التثبيت. لن يثبت WinKit البرامج أو يحذفها في الخلفية دون موافقتك.",
        "report_privacy_note": "يُنشأ التقرير محليًا وقد يحتوي على معلومات الجهاز ومحولات الشبكة. راجعه قبل مشاركته.",
        "safety_note": "الأمان: لا يعطل WinKit Defender أو Firewall أو Windows Update أو خدمات الحماية. تغييرات السجل محدودة بإعدادات المستخدم الحالي ولها نسخ احتياطية.",
        "temp_done": "انتهى تنظيف Temp. عناصر تمت معالجتها: {removed}، عناصر تم تخطيها: {skipped}.",
        "opened_settings": "تم فتح إعدادات Windows.", "opened_tool": "تم فتح أداة Windows.",
        "opened_terminal": "تم فتح نافذة الأوامر.", "uac_requested": "تم طلب صلاحية المسؤول عبر UAC. وافق عليها لإكمال التنفيذ.",
        "opened_powershell": "تم فتح PowerShell.", "dark_mode_done": "تم تفعيل الوضع الداكن لويندوز.",
        "light_mode_done": "تم تفعيل الوضع الفاتح لويندوز.", "restore_theme_done": "تمت استعادة {count} قيمة من إعدادات الألوان.",
        "restore_performance_done": "تمت استعادة {count} قيمة من إعدادات الأداء.",
        "low_end_applied": "تم تطبيق بريست الأداء للحساب الحالي. قد تحتاج إلى تسجيل الخروج أو إعادة تشغيل Explorer.",
        "disk_files_scanned": "الملفات التي تم فحصها: {count:,}", "disk_total": "الحجم الإجمالي: {size:.2f} GB",
        "largest_files": "أكبر الملفات:", "largest_types": "أكبر أنواع الملفات:",
        "skipped_files": "ملفات تعذر قراءتها: {count}", "clear_history_confirm": "هل تريد مسح سجل النشاط؟",
        "update_reminder": "شغّل «فحص التحديثات» أولًا وراجع القائمة قبل التحديث.",
        "import_prompt": "سيحاول WinGet تثبيت {count} برنامجًا من الملف التالي:\n{packages}\n\nراجع الملف ومصادر الحزم قبل الاستمرار. هل تريد المتابعة؟",
    },
    "en": {
        "app_subtitle": "Windows maintenance, diagnostics and productivity hub",
        "dashboard": "Dashboard", "tools": "Quick Tools", "cleanup": "Cleanup",
        "repair": "Smart Fix", "network": "Network", "performance": "Performance & Gaming",
        "hardware": "Hardware Monitor", "software": "Software Center", "disk": "Disk Analyzer",
        "report": "System Report", "favorites": "Favorites", "activity": "Activity Log",
        "settings": "Settings", "search": "Search tools or commands...", "language": "Language",
        "theme": "Theme", "welcome": "Your Windows toolkit, in one place",
        "welcome_sub": "Inspect your PC, troubleshoot issues and manage software from one interface.",
        "cpu": "CPU", "ram": "Memory", "disk_usage": "Disk", "uptime": "Uptime",
        "quick_actions": "Quick actions", "recent": "Recent activity", "all_tools": "All tools",
        "run": "Run", "copy": "Copy command", "favorite": "Add to favorites",
        "unfavorite": "Remove favorite", "safe": "Safe", "medium": "Moderate",
        "high": "High", "reversible": "Reversible", "no_results": "No matching tools found.",
        "ready": "Ready", "working": "Working...", "done": "Completed",
        "error": "Error", "confirm": "Confirm action", "cancel": "Cancel",
        "close": "Close", "save": "Save", "refresh": "Refresh", "open": "Open",
        "copy_done": "Command copied to clipboard.", "windows_only": "This feature is available on Windows only.",
        "dashboard_hint": "A quick overview of your PC and frequently used tools.",
        "fix_title": "Smart Fix Center", "fix_desc": "Run diagnostics first, then choose an appropriate repair.",
        "network_test": "Run network diagnostics", "network_test_desc": "Checks the local gateway, DNS and external connectivity.",
        "scan_running": "Scanning...", "scan_complete": "Scan complete.",
        "software_title": "Software Center", "software_desc": "Review installed apps and available updates through WinGet.",
        "installed_apps": "Installed apps", "check_updates": "Check updates",
        "update_all": "Update available apps", "export_apps": "Export app list", "import_apps": "Restore app list",
        "winget_missing": "WinGet was not found. Install App Installer from Microsoft Store, then retry.",
        "update_warning": "A command window will open and show available app updates. Review package prompts before approving installers. Continue?",
        "report_title": "System Report", "report_desc": "Create a local HTML report about this PC.",
        "generate_report": "Generate report", "report_saved": "Report saved.",
        "disk_title": "Disk Analyzer", "disk_desc": "Choose a folder to inspect large files and file types. Nothing is deleted.",
        "choose_folder": "Choose folder", "scan_folder": "Analyze folder", "scanning": "Scanning files...",
        "disk_empty": "Choose a folder to start the scan.", "hash_title": "SHA-256 Checker", "hash_desc": "Calculate a file hash to verify its integrity.",
        "choose_file": "Choose file", "hash_result": "SHA-256:",
        "performance_title": "Performance Studio", "performance_desc": "Careful presets with backups and an option to restore WinKit changes.",
        "low_end": "Low-end PC preset", "low_end_desc": "Reduces selected visual effects for the current user only. No FPS gain is guaranteed.",
        "restore": "Restore previous WinKit settings", "gaming": "Gaming settings",
        "battery": "Battery settings", "startup": "Manage startup apps",
        "theme_note": "This theme changes WinKit only, not Windows colors.",
        "appearance_note": "Changing Windows colors is a separate action in Quick Tools.",
        "activity_empty": "No actions have been run yet.", "settings_title": "Customize WinKit",
        "settings_desc": "Choose your interface language and preferred theme. Your choices are saved locally.",
        "theme_dark": "Dark Fluent", "theme_light": "Clean Light", "theme_midnight": "Midnight",
        "theme_graphite": "Graphite", "language_ar": "العربية", "language_en": "English",
        "language_fr": "Français", "restart_hint": "The interface language is applied immediately.",
        "command": "Command", "description": "Description", "risk": "Impact level",
        "admin_note": "Windows may request administrator approval through UAC.",
        "danger_note": "Review the impact before proceeding. Some operations cannot be undone.",
        "no_backup": "No backup exists for these settings.",
        "report_open": "Open report", "processes": "Top memory-consuming processes",
        "gpu_unavailable": "GPU readings are not available through generic system sensors on this device.",
        "metrics_unavailable": "Install requirements from requirements.txt to enable hardware monitoring.",
        "scan_limit": "The safe file-scan limit was reached.",
        "folder_error": "Some files could not be read due to permissions or file locks.",
        "quick_search_tip": "Search inside WinKit: Ctrl + K",
        "software_note": "WinGet may ask you to review installer agreements. WinKit does not silently install or remove apps.",
        "report_privacy_note": "The report is generated locally and may include device and network-adapter details. Review it before sharing.",
        "safety_note": "Safety: WinKit does not disable Defender, Firewall, Windows Update, or security services. Registry changes are limited to current-user preferences and are backed up.",
        "temp_done": "Temp cleanup finished. Items processed: {removed}; items skipped: {skipped}.",
        "opened_settings": "Windows settings opened.", "opened_tool": "Windows tool opened.",
        "opened_terminal": "A command window was opened.", "uac_requested": "Administrator approval was requested through UAC.",
        "opened_powershell": "PowerShell was opened.", "dark_mode_done": "Windows dark mode was enabled.",
        "light_mode_done": "Windows light mode was enabled.", "restore_theme_done": "Restored {count} Windows color preference values.",
        "restore_performance_done": "Restored {count} performance preference values.",
        "low_end_applied": "The performance preset was applied for the current user. Sign out or restart Explorer if needed.",
        "disk_files_scanned": "Files scanned: {count:,}", "disk_total": "Total size: {size:.2f} GB",
        "largest_files": "Largest files:", "largest_types": "Largest file types:",
        "skipped_files": "Unreadable files skipped: {count}", "clear_history_confirm": "Clear the activity history?",
        "update_reminder": "Run Check Updates first and review the list before updating.",
        "import_prompt": "WinGet will attempt to install {count} packages from this file:\n{packages}\n\nReview the manifest and package sources before continuing. Proceed?",
    },
    "fr": {
        "app_subtitle": "Centre de maintenance, diagnostic et productivité Windows",
        "dashboard": "Tableau de bord", "tools": "Outils rapides", "cleanup": "Nettoyage",
        "repair": "Réparation intelligente", "network": "Réseau", "performance": "Performances et jeux",
        "hardware": "Surveillance matériel", "software": "Centre logiciel", "disk": "Analyse disque",
        "report": "Rapport système", "favorites": "Favoris", "activity": "Historique",
        "settings": "Paramètres", "search": "Rechercher un outil ou une commande...", "language": "Langue",
        "theme": "Thème", "welcome": "Tous vos outils Windows au même endroit",
        "welcome_sub": "Analysez votre PC, diagnostiquez les problèmes et gérez les logiciels.",
        "cpu": "Processeur", "ram": "Mémoire", "disk_usage": "Disque", "uptime": "Durée active",
        "quick_actions": "Actions rapides", "recent": "Activité récente", "all_tools": "Tous les outils",
        "run": "Lancer", "copy": "Copier la commande", "favorite": "Ajouter aux favoris",
        "unfavorite": "Retirer des favoris", "safe": "Sûr", "medium": "Modéré",
        "high": "Élevé", "reversible": "Réversible", "no_results": "Aucun outil correspondant.",
        "ready": "Prêt", "working": "En cours...", "done": "Terminé",
        "error": "Erreur", "confirm": "Confirmer", "cancel": "Annuler",
        "close": "Fermer", "save": "Enregistrer", "refresh": "Actualiser", "open": "Ouvrir",
        "copy_done": "Commande copiée.", "windows_only": "Cette fonction est disponible uniquement sous Windows.",
        "dashboard_hint": "Aperçu rapide de votre PC et de vos outils fréquents.",
        "fix_title": "Centre de réparation", "fix_desc": "Lancez un diagnostic avant de choisir une réparation.",
        "network_test": "Diagnostiquer le réseau", "network_test_desc": "Vérifie la passerelle, le DNS et la connexion externe.",
        "scan_running": "Analyse...", "scan_complete": "Analyse terminée.",
        "software_title": "Centre logiciel", "software_desc": "Consultez les applications et mises à jour avec WinGet.",
        "installed_apps": "Applications installées", "check_updates": "Rechercher les mises à jour",
        "update_all": "Mettre à jour les applications", "export_apps": "Exporter la liste", "import_apps": "Restaurer la liste",
        "winget_missing": "WinGet introuvable. Installez App Installer depuis Microsoft Store.",
        "update_warning": "Une fenêtre de commande affichera les mises à jour. Vérifiez chaque demande d'installation. Continuer ?",
        "report_title": "Rapport système", "report_desc": "Créez un rapport HTML local de cet ordinateur.",
        "generate_report": "Créer le rapport", "report_saved": "Rapport enregistré.",
        "disk_title": "Analyseur de disque", "disk_desc": "Choisissez un dossier pour examiner les gros fichiers. Aucun fichier ne sera supprimé.",
        "choose_folder": "Choisir un dossier", "scan_folder": "Analyser", "scanning": "Analyse des fichiers...",
        "disk_empty": "Choisissez un dossier pour commencer.", "hash_title": "Vérificateur SHA-256", "hash_desc": "Calculez l'empreinte d'un fichier.",
        "choose_file": "Choisir un fichier", "hash_result": "SHA-256 :",
        "performance_title": "Studio de performances", "performance_desc": "Préréglages prudents avec sauvegarde et restauration.",
        "low_end": "Préréglage PC modeste", "low_end_desc": "Réduit certains effets visuels pour l'utilisateur actuel. Aucun gain FPS garanti.",
        "restore": "Restaurer les paramètres WinKit", "gaming": "Paramètres de jeu",
        "battery": "Paramètres de batterie", "startup": "Applications au démarrage",
        "theme_note": "Ce thème modifie uniquement WinKit, pas les couleurs de Windows.",
        "appearance_note": "Les couleurs de Windows se règlent séparément dans les outils rapides.",
        "activity_empty": "Aucune action exécutée pour le moment.", "settings_title": "Personnaliser WinKit",
        "settings_desc": "Choisissez la langue et le thème. Les préférences sont enregistrées localement.",
        "theme_dark": "Dark Fluent", "theme_light": "Clean Light", "theme_midnight": "Midnight",
        "theme_graphite": "Graphite", "language_ar": "العربية", "language_en": "English",
        "language_fr": "Français", "restart_hint": "La langue est appliquée immédiatement.",
        "command": "Commande", "description": "Description", "risk": "Niveau d'impact",
        "admin_note": "Windows peut demander les droits administrateur via UAC.",
        "danger_note": "Vérifiez l'impact. Certaines opérations sont irréversibles.",
        "no_backup": "Aucune sauvegarde n'existe pour ces paramètres.",
        "report_open": "Ouvrir le rapport", "processes": "Processus consommant le plus de mémoire",
        "gpu_unavailable": "Les capteurs système génériques ne fournissent pas de lecture GPU ici.",
        "metrics_unavailable": "Installez les dépendances depuis requirements.txt pour activer la surveillance.",
        "scan_limit": "La limite de sécurité du nombre de fichiers a été atteinte.",
        "folder_error": "Certains fichiers sont inaccessibles.",
        "quick_search_tip": "Recherche WinKit : Ctrl + K",
        "software_note": "WinGet peut demander de vérifier les accords d'installation. WinKit n'installe ni ne supprime silencieusement les applications.",
        "report_privacy_note": "Le rapport est créé localement et peut contenir des informations sur l'appareil et le réseau. Vérifiez-le avant de le partager.",
        "safety_note": "Sécurité : WinKit ne désactive pas Defender, le pare-feu, Windows Update ni les services de sécurité. Les modifications du registre sont limitées à l'utilisateur et sauvegardées.",
        "temp_done": "Nettoyage Temp terminé. Éléments traités : {removed} ; éléments ignorés : {skipped}.",
        "opened_settings": "Paramètres Windows ouverts.", "opened_tool": "Outil Windows ouvert.",
        "opened_terminal": "Une fenêtre de commande a été ouverte.", "uac_requested": "Une autorisation administrateur a été demandée via UAC.",
        "opened_powershell": "PowerShell a été ouvert.", "dark_mode_done": "Le mode sombre Windows est activé.",
        "light_mode_done": "Le mode clair Windows est activé.", "restore_theme_done": "{count} valeurs de couleur Windows ont été restaurées.",
        "restore_performance_done": "{count} valeurs de performance ont été restaurées.",
        "low_end_applied": "Le préréglage de performance a été appliqué à l'utilisateur actuel. Une reconnexion peut être nécessaire.",
        "disk_files_scanned": "Fichiers analysés : {count:,}", "disk_total": "Taille totale : {size:.2f} Go",
        "largest_files": "Fichiers les plus volumineux :", "largest_types": "Types de fichiers principaux :",
        "skipped_files": "Fichiers illisibles ignorés : {count}", "clear_history_confirm": "Effacer l'historique des actions ?",
        "update_reminder": "Lancez d'abord la recherche de mises à jour et vérifiez la liste.",
        "import_prompt": "WinGet va tenter d'installer {count} paquets depuis ce fichier :\n{packages}\n\nVérifiez le manifeste et les sources avant de continuer. Continuer ?",
    },
}

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#0B1020", "panel": "#111A2E", "card": "#17233B", "card2": "#1D2B45",
        "text": "#F3F6FC", "muted": "#A7B4CA", "accent": "#8B7CFF", "accent2": "#6255D9",
        "border": "#293956", "good": "#48D6A3", "warn": "#F4C66A", "bad": "#FF7F91",
    },
    "light": {
        "bg": "#F4F6FB", "panel": "#FFFFFF", "card": "#FFFFFF", "card2": "#EEF1F8",
        "text": "#20263A", "muted": "#68738A", "accent": "#6657D9", "accent2": "#5143BE",
        "border": "#DDE2EF", "good": "#138B69", "warn": "#A66B00", "bad": "#C43D55",
    },
    "midnight": {
        "bg": "#071522", "panel": "#0D2235", "card": "#123149", "card2": "#19415B",
        "text": "#EAF7FF", "muted": "#9AB8C9", "accent": "#35C4E8", "accent2": "#1494B7",
        "border": "#23506B", "good": "#4DDBB0", "warn": "#F3C36B", "bad": "#FF8094",
    },
    "graphite": {
        "bg": "#151719", "panel": "#202427", "card": "#292F32", "card2": "#343C3F",
        "text": "#F2F5F4", "muted": "#B0BCB8", "accent": "#39C98A", "accent2": "#239B67",
        "border": "#414B4D", "good": "#52D6A0", "warn": "#E9BF68", "bad": "#FF8590",
    },
}

# ---------------------------------------------------------------------------
# Action library. Commands are fixed, documented Windows entry points only.
# ---------------------------------------------------------------------------
ACTIONS: list[dict[str, Any]] = [
    {"id":"temp_cleanup","cat":"cleanup","icon":"🧹","title":"تنظيف ملفات Temp","en":"Clean user Temp files","fr":"Nettoyer les fichiers Temp","desc":"يحذف الملفات المؤقتة داخل مجلد المستخدم الحالي فقط. الملفات المستخدمة أو المحمية يتم تخطيها.","desc_en":"Removes items only from the current user's TEMP folder. Locked and protected items are skipped.","desc_fr":"Supprime uniquement les éléments du dossier TEMP de l'utilisateur actuel. Les fichiers verrouillés sont ignorés.","cmd":"%TEMP% (current user only)","kind":"temp","risk":"medium","confirm":True},
    {"id":"storage","cat":"cleanup","icon":"💽","title":"إعدادات مساحة التخزين","en":"Storage settings","fr":"Paramètres de stockage","desc":"يفتح إعدادات Storage Sense الرسمية لمراجعة المساحة والتنظيف يدويًا.","desc_en":"Opens official Storage Sense settings for review and manual cleanup.","desc_fr":"Ouvre les paramètres officiels de stockage.","cmd":"ms-settings:storagesense","kind":"uri","risk":"safe"},
    {"id":"recycle","cat":"cleanup","icon":"🗑️","title":"إفراغ سلة المحذوفات","en":"Empty Recycle Bin","fr":"Vider la corbeille","desc":"يفرغ سلة المحذوفات. راجع محتوياتها أولًا؛ لا يوجد تراجع عادي بعد الإفراغ.","desc_en":"Empties the Recycle Bin. Review its contents first; normal undo is not available.","desc_fr":"Vide la corbeille. Vérifiez son contenu avant de continuer.","cmd":"Clear-RecycleBin -Force","kind":"powershell","risk":"high","confirm":True},
    {"id":"disk_cleanup","cat":"cleanup","icon":"🧽","title":"أداة تنظيف القرص","en":"Disk Cleanup","fr":"Nettoyage de disque","desc":"يفتح أداة Windows Disk Cleanup لتختار بنفسك أنواع الملفات التي تريد مراجعتها.","desc_en":"Opens Windows Disk Cleanup so you can review categories before deleting.","desc_fr":"Ouvre l'outil Windows pour choisir les catégories à nettoyer.","cmd":"cleanmgr.exe","kind":"tool","risk":"safe"},
    {"id":"sfc","cat":"repair","icon":"🛠️","title":"فحص ملفات النظام SFC","en":"System File Checker (SFC)","fr":"Vérificateur de fichiers système","desc":"يفحص ملفات النظام المحمية ويحاول إصلاح التلف. قد يستغرق وقتًا ويطلب صلاحية المسؤول.","desc_en":"Scans protected Windows files and attempts repairs. May take time and requires elevation.","desc_fr":"Analyse les fichiers Windows protégés et tente de les réparer.","cmd":"sfc /scannow","kind":"admin","risk":"safe"},
    {"id":"dism","cat":"repair","icon":"🧰","title":"إصلاح صورة ويندوز DISM","en":"Repair Windows image (DISM)","fr":"Réparer l'image Windows (DISM)","desc":"يفحص مخزن مكونات Windows ويحاول إصلاحه. يتطلب صلاحية المسؤول واتصالًا بالإنترنت أحيانًا.","desc_en":"Checks and repairs the Windows component store. Administrator rights may be required.","desc_fr":"Vérifie et répare le magasin de composants Windows.","cmd":"DISM /Online /Cleanup-Image /RestoreHealth","kind":"admin","risk":"safe"},
    {"id":"update_settings","cat":"repair","icon":"🔄","title":"Windows Update","en":"Windows Update","fr":"Windows Update","desc":"يفتح صفحة التحديثات الرسمية وسجل التحديثات.","desc_en":"Opens official Windows Update settings and update history.","desc_fr":"Ouvre les paramètres officiels de mise à jour.","cmd":"ms-settings:windowsupdate","kind":"uri","risk":"safe"},
    {"id":"troubleshoot","cat":"repair","icon":"🩺","title":"مستكشف أخطاء ويندوز","en":"Windows troubleshooters","fr":"Dépanneurs Windows","desc":"يفتح صفحة مستكشفات الأخطاء الرسمية.","desc_en":"Opens official Windows troubleshooting settings.","desc_fr":"Ouvre les outils de dépannage Windows.","cmd":"ms-settings:troubleshoot","kind":"uri","risk":"safe"},
    {"id":"reliability","cat":"repair","icon":"📈","title":"سجل موثوقية النظام","en":"Reliability Monitor","fr":"Moniteur de fiabilité","desc":"يعرض سجل الأعطال والتثبيتات والأحداث المهمة على خط زمني.","desc_en":"Shows a timeline of app failures, installations and important system events.","desc_fr":"Affiche une chronologie des pannes et événements système.","cmd":"perfmon /rel","kind":"shell","risk":"safe"},
    {"id":"event_viewer","cat":"repair","icon":"📋","title":"عارض الأحداث","en":"Event Viewer","fr":"Observateur d'événements","desc":"يفتح سجل أحداث Windows لتفاصيل الأخطاء والتحذيرات.","desc_en":"Opens Windows event logs for error and warning details.","desc_fr":"Ouvre les journaux d'événements Windows.","cmd":"eventvwr.msc","kind":"shell","risk":"safe"},
    {"id":"flush_dns","cat":"network","icon":"🌐","title":"مسح DNS Cache","en":"Flush DNS cache","fr":"Vider le cache DNS","desc":"يمسح ذاكرة DNS المؤقتة، وقد يساعد عند تعطل الوصول لبعض المواقع.","desc_en":"Clears the DNS resolver cache and may help with stale domain lookups.","desc_fr":"Vide le cache DNS et peut résoudre des problèmes de résolution.","cmd":"ipconfig /flushdns","kind":"terminal","risk":"safe"},
    {"id":"ip_info","cat":"network","icon":"🧭","title":"معلومات الشبكة","en":"Network information","fr":"Informations réseau","desc":"يعرض عناوين IP وDNS ومعلومات محولات الشبكة.","desc_en":"Displays IP addresses, DNS and adapter details.","desc_fr":"Affiche les adresses IP, DNS et adaptateurs réseau.","cmd":"ipconfig /all","kind":"terminal","risk":"safe"},
    {"id":"network_settings","cat":"network","icon":"📶","title":"إعدادات الشبكة","en":"Network settings","fr":"Paramètres réseau","desc":"يفتح إعدادات الشبكة والإنترنت الرسمية.","desc_en":"Opens official Network & Internet settings.","desc_fr":"Ouvre les paramètres réseau officiels.","cmd":"ms-settings:network-status","kind":"uri","risk":"safe"},
    {"id":"winsock","cat":"network","icon":"🔌","title":"إعادة ضبط Winsock","en":"Reset Winsock","fr":"Réinitialiser Winsock","desc":"يعيد ضبط كتالوج Winsock. قد تحتاج لإعادة تشغيل الجهاز بعد التنفيذ.","desc_en":"Resets the Winsock catalog. A restart may be needed.","desc_fr":"Réinitialise Winsock. Un redémarrage peut être nécessaire.","cmd":"netsh winsock reset","kind":"admin","risk":"medium","confirm":True},
    {"id":"ip_reset","cat":"network","icon":"🛜","title":"إعادة ضبط TCP/IP","en":"Reset TCP/IP stack","fr":"Réinitialiser TCP/IP","desc":"يعيد إعدادات TCP/IP إلى حالتها الافتراضية. استخدمه فقط عند وجود مشكلة شبكة واضحة.","desc_en":"Resets TCP/IP settings. Use only when troubleshooting a real network issue.","desc_fr":"Réinitialise TCP/IP. À utiliser uniquement en cas de problème réseau confirmé.","cmd":"netsh int ip reset","kind":"admin","risk":"medium","confirm":True},
    {"id":"startup","cat":"performance","icon":"🚀","title":"تطبيقات بدء التشغيل","en":"Startup apps","fr":"Applications au démarrage","desc":"يفتح إدارة تطبيقات بدء التشغيل. راجع وظيفة كل تطبيق قبل تعطيله.","desc_en":"Opens startup app settings. Check what an app does before disabling it.","desc_fr":"Ouvre les applications au démarrage. Vérifiez chaque application avant désactivation.","cmd":"ms-settings:startupapps","kind":"uri","risk":"safe"},
    {"id":"power","cat":"performance","icon":"⚡","title":"إعدادات الطاقة","en":"Power settings","fr":"Paramètres d'alimentation","desc":"يفتح إعدادات الطاقة. أوضاع الأداء قد ترفع استهلاك الكهرباء والحرارة.","desc_en":"Opens power settings. Performance plans may increase power use and heat.","desc_fr":"Ouvre les paramètres d'alimentation. Les modes performants peuvent augmenter la chaleur.","cmd":"ms-settings:powersleep","kind":"uri","risk":"safe"},
    {"id":"game_mode","cat":"gaming","icon":"🎮","title":"إعدادات Game Mode","en":"Game Mode settings","fr":"Paramètres du mode Jeu","desc":"يفتح إعدادات وضع الألعاب. تأثيره يختلف حسب اللعبة والجهاز.","desc_en":"Opens Windows Game Mode settings. Its impact varies by PC and game.","desc_fr":"Ouvre les paramètres du mode Jeu. L'effet dépend du PC et du jeu.","cmd":"ms-settings:gaming-gamemode","kind":"uri","risk":"safe"},
    {"id":"graphics","cat":"gaming","icon":"🖥️","title":"إعدادات الرسومات","en":"Graphics settings","fr":"Paramètres graphiques","desc":"يفتح إعدادات الرسومات لاختيار تفضيل GPU لكل تطبيق عند دعم الجهاز.","desc_en":"Opens graphics preferences so you can select a GPU per app when supported.","desc_fr":"Ouvre les préférences graphiques par application.","cmd":"ms-settings:display-advancedgraphics","kind":"uri","risk":"safe"},
    {"id":"dark_windows","cat":"appearance","icon":"🌙","title":"تفعيل الوضع الداكن لويندوز","en":"Set Windows dark mode","fr":"Activer le mode sombre Windows","desc":"يغير تفضيل ألوان تطبيقات Windows والنظام للحساب الحالي مع نسخة احتياطية أولية.","desc_en":"Changes app and system theme preferences for the current user, keeping the original values for restore.","desc_fr":"Modifie le thème des applications et du système pour l'utilisateur actuel avec sauvegarde.","cmd":"AppsUseLightTheme=0; SystemUsesLightTheme=0","kind":"dark_theme","risk":"reversible"},
    {"id":"light_windows","cat":"appearance","icon":"☀️","title":"تفعيل الوضع الفاتح لويندوز","en":"Set Windows light mode","fr":"Activer le mode clair Windows","desc":"يغير تفضيل الألوان إلى الفاتح للحساب الحالي مع إمكانية الاستعادة.","desc_en":"Changes theme preferences to light for the current user with restore support.","desc_fr":"Passe le thème en mode clair avec possibilité de restauration.","cmd":"AppsUseLightTheme=1; SystemUsesLightTheme=1","kind":"light_theme","risk":"reversible"},
    {"id":"restore_theme","cat":"appearance","icon":"↩️","title":"استعادة ألوان ويندوز السابقة","en":"Restore previous Windows colors","fr":"Restaurer les couleurs Windows","desc":"يرجع تفضيلات الألوان التي حفظها WinKit قبل أول تغيير.","desc_en":"Restores the color preferences WinKit backed up before its first change.","desc_fr":"Restaure les préférences sauvegardées avant la première modification.","cmd":"Restore WinKit theme backup","kind":"restore_theme","risk":"safe"},
    {"id":"personalize","cat":"appearance","icon":"🎨","title":"إعدادات التخصيص","en":"Personalization settings","fr":"Paramètres de personnalisation","desc":"يفتح إعدادات الخلفية والألوان والثيمات الرسمية.","desc_en":"Opens official background, color and theme settings.","desc_fr":"Ouvre les paramètres officiels de fond, couleurs et thèmes.","cmd":"ms-settings:personalization","kind":"uri","risk":"safe"},
    {"id":"bluetooth","cat":"shortcuts","icon":"🟦","title":"إعدادات Bluetooth","en":"Bluetooth settings","fr":"Paramètres Bluetooth","desc":"يفتح إعدادات البلوتوث وإضافة الأجهزة.","desc_en":"Opens Bluetooth settings and device pairing.","desc_fr":"Ouvre les paramètres Bluetooth et l'association des appareils.","cmd":"ms-settings:bluetooth","kind":"uri","risk":"safe"},
    {"id":"sound","cat":"shortcuts","icon":"🔊","title":"إعدادات الصوت","en":"Sound settings","fr":"Paramètres audio","desc":"يفتح أجهزة الإدخال والإخراج ومستوى الصوت.","desc_en":"Opens input, output and volume settings.","desc_fr":"Ouvre les paramètres d'entrée, sortie et volume.","cmd":"ms-settings:sound","kind":"uri","risk":"safe"},
    {"id":"privacy","cat":"shortcuts","icon":"🔒","title":"إعدادات الخصوصية","en":"Privacy settings","fr":"Paramètres de confidentialité","desc":"يفتح إعدادات أذونات التطبيقات والخصوصية لمراجعتها.","desc_en":"Opens app permissions and privacy controls for review.","desc_fr":"Ouvre les autorisations des applications et les contrôles de confidentialité.","cmd":"ms-settings:privacy","kind":"uri","risk":"safe"},
    {"id":"firewall","cat":"shortcuts","icon":"🛡️","title":"أمان Windows وجدار الحماية","en":"Windows Security and Firewall","fr":"Sécurité Windows et pare-feu","desc":"يفتح تطبيق أمان Windows لمراجعة حالة جدار الحماية والحماية. لا يعطل أي إعداد.","desc_en":"Opens Windows Security to review firewall and protection status. It does not disable settings.","desc_fr":"Ouvre Sécurité Windows pour vérifier le pare-feu et les protections sans les désactiver.","cmd":"windowsdefender:","kind":"uri","risk":"safe"},
    {"id":"optional_features","cat":"shortcuts","icon":"🧱","title":"ميزات Windows الاختيارية","en":"Optional Windows features","fr":"Fonctionnalités facultatives Windows","desc":"يفتح إدارة ميزات Windows الاختيارية.","desc_en":"Opens optional Windows features management.","desc_fr":"Ouvre la gestion des fonctionnalités facultatives.","cmd":"optionalfeatures.exe","kind":"shell","risk":"medium"},
    {"id":"memory_diagnostic","cat":"repair","icon":"🧠","title":"تشخيص ذاكرة RAM","en":"Windows Memory Diagnostic","fr":"Diagnostic de mémoire Windows","desc":"يفتح أداة تشخيص الذاكرة المدمجة. قد تتطلب إعادة تشغيل الجهاز لإجراء الفحص.","desc_en":"Opens the built-in memory diagnostic. A restart may be required to run the test.","desc_fr":"Ouvre le diagnostic mémoire intégré. Un redémarrage peut être nécessaire.","cmd":"mdsched.exe","kind":"shell","risk":"medium","confirm":True},
    {"id":"taskmgr","cat":"shortcuts","icon":"📊","title":"مدير المهام","en":"Task Manager","fr":"Gestionnaire des tâches","desc":"يراجع استخدام CPU والذاكرة والقرص والعمليات.","desc_en":"Reviews CPU, memory, disk and process usage.","desc_fr":"Affiche l'utilisation du processeur, mémoire, disque et processus.","cmd":"taskmgr","kind":"shell","risk":"safe"},
    {"id":"resmon","cat":"shortcuts","icon":"📉","title":"مراقب الموارد","en":"Resource Monitor","fr":"Moniteur de ressources","desc":"يعرض تفاصيل موارد النظام والعمليات والشبكة.","desc_en":"Shows detailed resource, process and network activity.","desc_fr":"Affiche les détails des ressources, processus et du réseau.","cmd":"resmon","kind":"shell","risk":"safe"},
    {"id":"devmgr","cat":"shortcuts","icon":"🧩","title":"إدارة الأجهزة","en":"Device Manager","fr":"Gestionnaire de périphériques","desc":"يراجع حالة الأجهزة والتعريفات. لا تحذف تعريفًا دون معرفة السبب.","desc_en":"Reviews device and driver status. Do not remove drivers without a reason.","desc_fr":"Vérifie les périphériques et pilotes. Ne supprimez pas un pilote sans raison.","cmd":"devmgmt.msc","kind":"shell","risk":"safe"},
    {"id":"programs","cat":"shortcuts","icon":"📦","title":"التطبيقات المثبتة","en":"Installed apps","fr":"Applications installées","desc":"يفتح إعدادات التطبيقات لإزالة البرامج بالطريقة الرسمية.","desc_en":"Opens installed apps settings for normal uninstallation.","desc_fr":"Ouvre les paramètres des applications installées.","cmd":"ms-settings:appsfeatures","kind":"uri","risk":"safe"},
    {"id":"display","cat":"shortcuts","icon":"🖥️","title":"إعدادات الشاشة","en":"Display settings","fr":"Paramètres d'affichage","desc":"يفتح إعدادات الدقة والشاشات ومعدل التحديث عند دعمه.","desc_en":"Opens resolution, displays and refresh-rate settings where supported.","desc_fr":"Ouvre les paramètres de résolution et d'affichage.","cmd":"ms-settings:display","kind":"uri","risk":"safe"},
    {"id":"services","cat":"shortcuts","icon":"⚙️","title":"خدمات ويندوز","en":"Windows Services","fr":"Services Windows","desc":"يفتح قائمة الخدمات. تغيير خدمات النظام عشوائيًا قد يسبب مشاكل.","desc_en":"Opens Services. Randomly changing system services can cause problems.","desc_fr":"Ouvre les services. Les modifications aléatoires peuvent causer des problèmes.","cmd":"services.msc","kind":"shell","risk":"medium"},
    {"id":"diskmgmt","cat":"shortcuts","icon":"💾","title":"إدارة الأقراص","en":"Disk Management","fr":"Gestion des disques","desc":"يفتح إدارة الأقراص. انتبه جيدًا قبل تغيير الأقسام أو تهيئتها.","desc_en":"Opens Disk Management. Be careful before changing or formatting partitions.","desc_fr":"Ouvre la gestion des disques. Attention avant de modifier ou formater une partition.","cmd":"diskmgmt.msc","kind":"shell","risk":"medium"},
    {"id":"msinfo","cat":"shortcuts","icon":"ℹ️","title":"معلومات النظام","en":"System Information","fr":"Informations système","desc":"يفتح ملخص مكونات الجهاز والموارد والبيئة البرمجية.","desc_en":"Opens a summary of hardware, resources and software environment.","desc_fr":"Affiche un résumé du matériel et de l'environnement logiciel.","cmd":"msinfo32","kind":"shell","risk":"safe"},
    {"id":"dxdiag","cat":"shortcuts","icon":"🎛️","title":"تشخيص DirectX","en":"DirectX Diagnostic Tool","fr":"Outil de diagnostic DirectX","desc":"يعرض معلومات كرت الشاشة والصوت وإصدار DirectX.","desc_en":"Shows graphics, audio and DirectX information.","desc_fr":"Affiche les informations graphiques, audio et DirectX.","cmd":"dxdiag","kind":"shell","risk":"safe"},
]

CATEGORY_KEYS = ["all", "cleanup", "repair", "network", "performance", "gaming", "appearance", "shortcuts"]
CATEGORY_TRANSLATIONS = {
    "ar": {"all":"كل الأدوات", "cleanup":"التنظيف", "repair":"الإصلاح", "network":"الشبكة", "performance":"الأداء", "gaming":"الألعاب", "appearance":"التخصيص", "shortcuts":"اختصارات النظام"},
    "en": {"all":"All tools", "cleanup":"Cleanup", "repair":"Repair", "network":"Network", "performance":"Performance", "gaming":"Gaming", "appearance":"Personalization", "shortcuts":"System shortcuts"},
    "fr": {"all":"Tous les outils", "cleanup":"Nettoyage", "repair":"Réparation", "network":"Réseau", "performance":"Performances", "gaming":"Jeux", "appearance":"Personnalisation", "shortcuts":"Raccourcis système"},
}

# ---------------------------------------------------------------------------
# Local settings, activity log and registry backups
# ---------------------------------------------------------------------------
def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load_settings() -> dict[str, Any]:
    data = read_json(SETTINGS_PATH, {})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("language", "ar")
    data.setdefault("theme", "dark")
    data.setdefault("favorites", [])
    data.setdefault("recent", [])
    return data


def add_activity(settings: dict[str, Any], action_id: str, status: str = "started") -> None:
    history = settings.setdefault("recent", [])
    history.insert(0, {"id": action_id, "time": datetime.now().isoformat(timespec="seconds"), "status": status})
    settings["recent"] = history[:30]
    write_json(SETTINGS_PATH, settings)


def is_windows() -> bool:
    return sys.platform == "win32"


def capture_registry_group(group: str, values: list[tuple[str, str, Any, str]]) -> None:
    if not is_windows():
        raise RuntimeError("Registry changes are available on Windows only.")
    import winreg
    backups = read_json(BACKUP_PATH, {})
    if group in backups:
        return
    entries = []
    for path, name, _new_value, _kind in values:
        entry = {"path": path, "name": name, "exists": False}
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as key:
                old_value, old_type = winreg.QueryValueEx(key, name)
                entry.update({"exists": True, "value": old_value, "type": old_type})
        except FileNotFoundError:
            pass
        entries.append(entry)
    backups[group] = entries
    write_json(BACKUP_PATH, backups)


def apply_registry_group(group: str, values: list[tuple[str, str, Any, str]]) -> None:
    if not is_windows():
        raise RuntimeError("Registry changes are available on Windows only.")
    import winreg
    capture_registry_group(group, values)
    for path, name, value, kind in values:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            vtype = winreg.REG_DWORD if kind == "DWORD" else winreg.REG_SZ
            winreg.SetValueEx(key, name, 0, vtype, value)


def restore_registry_group(group: str) -> int:
    if not is_windows():
        raise RuntimeError("Registry changes are available on Windows only.")
    import winreg
    backups = read_json(BACKUP_PATH, {})
    entries = backups.get(group)
    if not entries:
        raise RuntimeError("لا توجد نسخة احتياطية محفوظة لهذه الإعدادات.")
    restored = 0
    for entry in entries:
        path, name = entry["path"], entry["name"]
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            if entry.get("exists"):
                winreg.SetValueEx(key, name, 0, int(entry["type"]), entry["value"])
            else:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
        restored += 1
    backups.pop(group, None)
    write_json(BACKUP_PATH, backups)
    return restored


PERFORMANCE_VALUES = [
    (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0, "DWORD"),
    (r"Control Panel\Desktop\WindowMetrics", "MinAnimate", "0", "SZ"),
    (r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2, "DWORD"),
]
THEME_DARK = [
    (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 0, "DWORD"),
    (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", 0, "DWORD"),
]
THEME_LIGHT = [
    (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 1, "DWORD"),
    (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", 1, "DWORD"),
]


def clean_user_temp() -> tuple[int, int]:
    """Delete only current-user TEMP entries without traversing reparse points."""
    temp_path = Path(tempfile.gettempdir()).resolve()
    local_appdata = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))).resolve()
    profile = Path.home().resolve()
    try:
        allowed = temp_path.is_relative_to(local_appdata) or temp_path.is_relative_to(profile)
    except (AttributeError, OSError):
        allowed = str(local_appdata).casefold() in str(temp_path).casefold() or str(profile).casefold() in str(temp_path).casefold()
    if not allowed:
        raise RuntimeError("تعذر التحقق من مجلد Temp الخاص بالمستخدم. لم يتم حذف أي شيء.")
    if not temp_path.exists() or temp_path == Path(temp_path.anchor):
        raise RuntimeError("مسار Temp غير صالح. لم يتم حذف أي شيء.")

    reparse_flag = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    removed = 0
    skipped = 0

    def remove_tree(folder: Path) -> None:
        nonlocal removed, skipped
        for entry in os.scandir(folder):
            path = Path(entry.path)
            try:
                meta = entry.stat(follow_symlinks=False)
                if entry.is_symlink() or (getattr(meta, "st_file_attributes", 0) & reparse_flag):
                    skipped += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    remove_tree(path)
                    try:
                        path.rmdir()
                        removed += 1
                    except OSError:
                        skipped += 1
                else:
                    path.unlink()
                    removed += 1
            except OSError:
                skipped += 1

    for child in temp_path.iterdir():
        try:
            meta = child.lstat()
            if child.is_symlink() or (getattr(meta, "st_file_attributes", 0) & reparse_flag):
                skipped += 1
                continue
            if child.is_dir():
                remove_tree(child)
                try:
                    child.rmdir()
                    removed += 1
                except OSError:
                    skipped += 1
            else:
                child.unlink(missing_ok=True)
                removed += 1
        except OSError:
            skipped += 1
    return removed, skipped


def run_admin(command: str) -> None:
    if not is_windows():
        raise RuntimeError("Administrator commands are available on Windows only.")
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f'/k "{command}"', None, 1)
    if result <= 32:
        raise OSError(f"تعذر فتح نافذة المسؤول (Windows code {result}).")


def launch_action(action: dict[str, Any], lang: str = "ar") -> str:
    if not is_windows():
        raise RuntimeError(TEXTS.get(lang, TEXTS["en"])["windows_only"])
    tx = TEXTS.get(lang, TEXTS["en"])
    kind, command = action["kind"], action["cmd"]
    if kind == "uri":
        QDesktopServices.openUrl(QUrl(command))
        return tx["opened_settings"]
    if kind == "shell" or kind == "tool":
        subprocess.Popen(command, shell=True)
        return tx["opened_tool"]
    if kind == "terminal":
        subprocess.Popen(["cmd.exe", "/k", command], creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        return tx["opened_terminal"]
    if kind == "admin":
        run_admin(command)
        return tx["uac_requested"]
    if kind == "powershell":
        subprocess.Popen(["powershell.exe", "-NoProfile", "-NoExit", "-Command", command], creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        return tx["opened_powershell"]
    if kind == "temp":
        removed, skipped = clean_user_temp()
        return tx["temp_done"].format(removed=removed, skipped=skipped)
    if kind == "dark_theme":
        apply_registry_group("windows_theme", THEME_DARK)
        return tx["dark_mode_done"]
    if kind == "light_theme":
        apply_registry_group("windows_theme", THEME_LIGHT)
        return tx["light_mode_done"]
    if kind == "restore_theme":
        count = restore_registry_group("windows_theme")
        return tx["restore_theme_done"].format(count=count)
    raise RuntimeError("نوع الأداة غير معروف.")


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------
class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.fn())
        except Exception as exc:
            self.signals.error.emit(str(exc))


def scan_folder(folder: Path, limit: int = 50000) -> dict[str, Any]:
    root_meta = folder.lstat()
    root_reparse = getattr(root_meta, "st_file_attributes", 0) & getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if folder.is_symlink() or root_reparse:
        raise RuntimeError("The selected folder is a symbolic link or reparse point. Choose its real folder path instead.")
    files: list[tuple[int, str]] = []
    extensions: Counter[str] = Counter()
    total_bytes = 0
    errors = 0
    scanned = 0
    reparse_flag = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    for root, dirs, names in os.walk(folder, followlinks=False):
        safe_dirs = []
        for d in dirs:
            candidate = Path(root) / d
            try:
                meta = candidate.lstat()
                if candidate.is_symlink() or (getattr(meta, "st_file_attributes", 0) & reparse_flag):
                    continue
                safe_dirs.append(d)
            except OSError:
                continue
        dirs[:] = safe_dirs
        for name in names:
            path = Path(root) / name
            try:
                meta = path.lstat()
                if path.is_symlink() or (getattr(meta, "st_file_attributes", 0) & reparse_flag):
                    continue
                size = meta.st_size
                total_bytes += size
                scanned += 1
                ext = path.suffix.lower() or "[no extension]"
                extensions[ext] += size
                files.append((size, str(path)))
                if scanned >= limit:
                    break
            except OSError:
                errors += 1
        if scanned >= limit:
            break
    files.sort(reverse=True)
    return {"scanned": scanned, "total": total_bytes, "largest": files[:20], "extensions": extensions.most_common(12), "errors": errors, "limited": scanned >= limit}


def make_system_report() -> str:
    lines: list[tuple[str, str]] = []
    lines.append(("Computer", platform.node()))
    lines.append(("Operating system", platform.platform()))
    lines.append(("Windows version", platform.version()))
    lines.append(("Architecture", platform.machine()))
    lines.append(("Processor", platform.processor() or "Not reported"))
    lines.append(("Python", sys.version.split()[0]))
    if psutil:
        vm = psutil.virtual_memory()
        lines.extend([("Physical memory", f"{vm.total / (1024**3):.2f} GB"), ("Memory in use", f"{vm.percent:.1f}%")])
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                lines.append((f"Disk {part.device}", f"{usage.used / (1024**3):.1f} / {usage.total / (1024**3):.1f} GB ({usage.percent:.1f}%)"))
            except OSError:
                pass
        for name, addrs in psutil.net_if_addrs().items():
            ips = [a.address for a in addrs if getattr(a.family, "name", "") in ("AF_INET", "AF_INET6")]
            if ips:
                lines.append((f"Network: {name}", ", ".join(ips)))
    if is_windows() and shutil.which("winget"):
        try:
            proc = subprocess.run(["winget", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=35)
            lines.append(("WinGet installed apps", proc.stdout[-12000:] if proc.stdout else proc.stderr[-3000:]))
        except Exception as exc:
            lines.append(("WinGet", f"Could not read app list: {exc}"))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = "".join(f"<tr><th>{html.escape(k)}</th><td><pre>{html.escape(v)}</pre></td></tr>" for k, v in lines)
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>WinKit System Report</title>
<style>body{{font:15px Segoe UI,Arial;background:#f4f6fb;color:#20263a;margin:32px}}h1{{color:#5143be}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:12px;border-bottom:1px solid #dde2ef;text-align:left;vertical-align:top}}th{{width:220px;color:#5143be}}pre{{white-space:pre-wrap;margin:0;font:13px Consolas,monospace}}small{{color:#68738a}}</style></head><body>
<h1>WinKit System Report</h1><small>Generated: {html.escape(generated)} · This report is stored locally.</small><table>{rows}</table></body></html>"""


def network_diagnostics() -> str:
    results: list[str] = []
    if not is_windows():
        return "Network diagnostics are intended for Windows."
    try:
        proc = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        results.append("[IP CONFIG]\n" + (proc.stdout or proc.stderr)[:5000])
    except Exception as exc:
        results.append(f"[IP CONFIG] {exc}")
    try:
        ip = socket.gethostbyname("example.com")
        results.append(f"[DNS] OK: example.com resolved to {ip}")
    except Exception as exc:
        results.append(f"[DNS] FAILED: {exc}")
    try:
        started = time.monotonic()
        with socket.create_connection(("1.1.1.1", 53), timeout=3):
            elapsed = (time.monotonic() - started) * 1000
        results.append(f"[INTERNET] TCP connection to 1.1.1.1:53 succeeded ({elapsed:.0f} ms)")
    except Exception as exc:
        results.append(f"[INTERNET] Could not connect to 1.1.1.1:53: {exc}")
    return "\n\n".join(results)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "--", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(112)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Muted")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(7)
        lay.addWidget(self.title_label)
        lay.addWidget(self.value_label)
        lay.addStretch(1)
        lay.addWidget(self.progress)

    def update_value(self, title: str, percent: float, display: str) -> None:
        self.title_label.setText(title)
        self.value_label.setText(display)
        self.progress.setValue(max(0, min(100, int(percent))))


class ToolCard(QFrame):
    run_requested = Signal(str)
    favorite_requested = Signal(str)
    copy_requested = Signal(str)

    def __init__(self, action: dict[str, Any], lang: str, theme: dict[str, str], favorite: bool = False):
        super().__init__()
        self.action = action
        self.lang = lang
        self.theme = theme
        self.setObjectName("ToolCard")
        self.setProperty("class", "ToolCard")
        self.setMinimumHeight(205)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(8)
        top = QHBoxLayout()
        icon = QLabel(action["icon"])
        icon.setObjectName("ToolIcon")
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(icon)
        top.addStretch(1)
        self.fav_btn = QPushButton("★" if favorite else "☆")
        self.fav_btn.setObjectName("IconButton")
        self.fav_btn.setToolTip(TEXTS[lang]["unfavorite"] if favorite else TEXTS[lang]["favorite"])
        self.fav_btn.clicked.connect(lambda: self.favorite_requested.emit(action["id"]))
        top.addWidget(self.fav_btn)
        outer.addLayout(top)
        title = QLabel(self.title())
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        outer.addWidget(title)
        desc = QLabel(self.description())
        desc.setObjectName("Muted")
        desc.setWordWrap(True)
        desc.setMinimumHeight(42)
        outer.addWidget(desc)
        cmd = QLabel(action["cmd"])
        cmd.setObjectName("CommandLabel")
        cmd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd.setWordWrap(True)
        outer.addWidget(cmd)
        bottom = QHBoxLayout()
        risk_key = {"safe":"safe", "medium":"medium", "high":"high", "reversible":"reversible"}.get(action["risk"], "safe")
        risk_label = QLabel(TEXTS[lang][risk_key])
        risk_label.setObjectName("Risk")
        bottom.addWidget(risk_label)
        bottom.addStretch(1)
        copy_btn = QPushButton(TEXTS[lang]["copy"])
        copy_btn.setObjectName("SecondaryButton")
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(action["id"]))
        run_btn = QPushButton(TEXTS[lang]["run"])
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(lambda: self.run_requested.emit(action["id"]))
        bottom.addWidget(copy_btn)
        bottom.addWidget(run_btn)
        outer.addLayout(bottom)

    def title(self) -> str:
        return self.action["title"] if self.lang == "ar" else self.action.get(self.lang, self.action.get("en", ""))

    def description(self) -> str:
        return self.action["desc"] if self.lang == "ar" else self.action.get("desc_" + self.lang, self.action["desc_en"])


class AnimatedPage(QStackedWidget):
    def __init__(self):
        super().__init__()
        self._animation: QPropertyAnimation | None = None

    def show_page(self, page: QWidget) -> None:
        self.setCurrentWidget(page)
        effect = page.graphicsEffect()
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        if effect is None or not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        if self._animation is not None:
            self._animation.stop()
            self._animation.deleteLater()
        self._animation = QPropertyAnimation(effect, b"opacity", self)
        self._animation.finished.connect(self._animation.deleteLater)
        self._animation.setDuration(190)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.start()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class WinKitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.settings = load_settings()
        self.lang = self.settings.get("language", "ar") if self.settings.get("language") in TEXTS else "ar"
        self.theme_name = self.settings.get("theme", "dark") if self.settings.get("theme") in THEMES else "dark"
        self.theme = THEMES[self.theme_name]
        self.thread_pool = QThreadPool.globalInstance()
        self.current_page = "dashboard"
        self.current_category = "all"
        self.query = ""
        self.software_update_previewed = False
        self.metric_cards: dict[str, MetricCard] = {}
        self.setWindowTitle(f"WinKit {APP_VERSION}")
        self.setMinimumSize(1020, 680)
        self.resize(1360, 860)
        self._build_ui()
        self._apply_theme()
        self._setup_shortcuts()
        self.refresh_metrics()
        self.metric_timer = QTimer(self)
        self.metric_timer.timeout.connect(self.refresh_metrics)
        self.metric_timer.start(2200)

    def tr(self, key: str) -> str:
        return TEXTS[self.lang].get(key, key)

    def _setup_shortcuts(self) -> None:
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(lambda: self.search_box.setFocus())
        self.search_shortcut.activated.connect(lambda: self.search_box.selectAll())
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(lambda: self.search_box.clear())

    def _build_ui(self) -> None:
        old = self.takeCentralWidget()
        if old:
            old.deleteLater()
        root = QWidget()
        root.setObjectName("Root")
        shell = QHBoxLayout(root)
        shell.setContentsMargins(16, 16, 16, 16)
        shell.setSpacing(14)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(226)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(14, 18, 14, 16)
        side.setSpacing(7)
        brand = QHBoxLayout()
        logo = QLabel("W")
        logo.setObjectName("LogoMark")
        logo.setFixedSize(42, 42)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_text = QVBoxLayout()
        name = QLabel("WinKit")
        name.setObjectName("BrandName")
        subtitle = QLabel(self.tr("app_subtitle"))
        subtitle.setObjectName("TinyMuted")
        subtitle.setWordWrap(True)
        brand_text.addWidget(name)
        brand_text.addWidget(subtitle)
        brand.addWidget(logo)
        brand.addLayout(brand_text, 1)
        side.addLayout(brand)
        side.addSpacing(20)

        self.nav_buttons: dict[str, QPushButton] = {}
        nav_items = [
            ("dashboard", "▦", self.tr("dashboard")), ("tools", "⌘", self.tr("tools")),
            ("repair", "✚", self.tr("repair")), ("performance", "◈", self.tr("performance")),
            ("hardware", "◉", self.tr("hardware")), ("software", "▣", self.tr("software")),
            ("disk", "◫", self.tr("disk")), ("report", "▤", self.tr("report")),
            ("favorites", "☆", self.tr("favorites")), ("activity", "◷", self.tr("activity")),
        ]
        for key, symbol, label in nav_items:
            b = QPushButton(f"{symbol}   {label}")
            b.setObjectName("NavButton")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked=False, k=key: self.navigate(k))
            self.nav_buttons[key] = b
            side.addWidget(b)
        side.addStretch(1)
        settings_btn = QPushButton(f"⚙   {self.tr('settings')}")
        settings_btn.setObjectName("NavButton")
        settings_btn.clicked.connect(lambda: self.navigate("settings"))
        side.addWidget(settings_btn)
        footer = QLabel(f"WinKit {APP_VERSION}  •  Windows 10/11")
        footer.setObjectName("TinyMuted")
        side.addWidget(footer)
        shell.addWidget(self.sidebar)

        main_area = QVBoxLayout()
        main_area.setSpacing(12)
        topbar = QHBoxLayout()
        self.page_heading = QLabel(self.tr("dashboard"))
        self.page_heading.setObjectName("PageHeading")
        topbar.addWidget(self.page_heading)
        topbar.addStretch(1)
        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText(self.tr("search"))
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setFixedWidth(330)
        self.search_box.textChanged.connect(self.on_search_changed)
        topbar.addWidget(self.search_box)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("TopCombo")
        self._fill_theme_combo()
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        topbar.addWidget(self.theme_combo)
        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName("TopCombo")
        self.lang_combo.addItem("العربية", "ar")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Français", "fr")
        self.lang_combo.setCurrentIndex(["ar", "en", "fr"].index(self.lang))
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        topbar.addWidget(self.lang_combo)
        main_area.addLayout(topbar)

        self.pages = AnimatedPage()
        self.page_widgets: dict[str, QWidget] = {}
        for key, builder in [
            ("dashboard", self.build_dashboard), ("tools", self.build_tools),
            ("repair", self.build_repair), ("performance", self.build_performance),
            ("hardware", self.build_hardware), ("software", self.build_software),
            ("disk", self.build_disk), ("report", self.build_report),
            ("favorites", self.build_favorites), ("activity", self.build_activity),
            ("settings", self.build_settings),
        ]:
            page = builder()
            self.page_widgets[key] = page
            self.pages.addWidget(page)
        main_area.addWidget(self.pages, 1)
        self.status_label = QLabel(self.tr("ready"))
        self.status_label.setObjectName("StatusBar")
        main_area.addWidget(self.status_label)
        shell.addLayout(main_area, 1)
        self.setCentralWidget(root)
        self.navigate(self.current_page, animate=False)

    def _fill_theme_combo(self) -> None:
        if not hasattr(self, "theme_combo"):
            return
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for k, label in [("dark", "Dark Fluent"), ("light", "Clean Light"), ("midnight", "Midnight"), ("graphite", "Graphite")]:
            self.theme_combo.addItem(label, k)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.theme_name)))
        self.theme_combo.blockSignals(False)

    def _apply_theme(self) -> None:
        c = self.theme
        self.setStyleSheet(f"""
        QWidget#Root {{ background: {c['bg']}; color: {c['text']}; font-family: 'Segoe UI'; font-size: 10pt; }}
        QFrame#Sidebar {{ background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 18px; }}
        QLabel {{ color: {c['text']}; }}
        QLabel#BrandName {{ font-size: 20pt; font-weight: 800; }}
        QLabel#LogoMark {{ background: {c['accent']}; color: white; border-radius: 13px; font-size: 21pt; font-weight: 900; }}
        QLabel#TinyMuted {{ color: {c['muted']}; font-size: 8pt; }}
        QLabel#Muted {{ color: {c['muted']}; }}
        QLabel#PageHeading {{ font-size: 19pt; font-weight: 750; }}
        QLabel#MetricValue {{ font-size: 23pt; font-weight: 800; }}
        QLabel#CardTitle {{ font-size: 11pt; font-weight: 700; }}
        QLabel#ToolIcon {{ font-size: 20pt; background: {c['card2']}; border-radius: 12px; }}
        QLabel#CommandLabel {{ color: {c['accent']}; background: {c['card2']}; border-radius: 7px; padding: 6px; font-family: Consolas; font-size: 8pt; }}
        QLabel#StatusBar {{ color: {c['muted']}; background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 7px 12px; }}
        QLabel#Risk {{ color: {c['warn']}; font-size: 8pt; font-weight: 700; }}
        QFrame#Card, QFrame#ToolCard {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 15px; }}
        QFrame#ToolCard:hover {{ border: 1px solid {c['accent']}; background: {c['card2']}; }}
        QPushButton {{ color: {c['text']}; background: {c['card2']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 9px 13px; font-weight: 600; }}
        QPushButton:hover {{ border-color: {c['accent']}; background: {c['card']}; }}
        QPushButton:pressed {{ background: {c['accent2']}; }}
        QPushButton#PrimaryButton {{ color: white; background: {c['accent2']}; border: 1px solid {c['accent']}; }}
        QPushButton#PrimaryButton:hover {{ background: {c['accent']}; }}
        QPushButton#SecondaryButton {{ background: {c['card2']}; }}
        QPushButton#IconButton {{ border: none; background: transparent; font-size: 15pt; padding: 4px; }}
        QPushButton#NavButton {{ text-align: left; padding: 11px 12px; border: none; background: transparent; color: {c['muted']}; border-radius: 9px; }}
        QPushButton#NavButton:hover {{ background: {c['card2']}; color: {c['text']}; }}
        QPushButton#NavButton[active="true"] {{ background: {c['accent2']}; color: white; }}
        QLineEdit, QComboBox, QPlainTextEdit {{ color: {c['text']}; background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 9px 11px; selection-background-color: {c['accent2']}; }}
        QComboBox QAbstractItemView {{ background: {c['panel']}; color: {c['text']}; selection-background-color: {c['accent2']}; }}
        QProgressBar {{ background: {c['card2']}; border: none; border-radius: 4px; }}
        QProgressBar::chunk {{ background: {c['accent']}; border-radius: 4px; }}
        QScrollArea {{ border: none; background: transparent; }}
        QCheckBox {{ spacing: 8px; }}
        """)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.lang == "ar" else Qt.LayoutDirection.LeftToRight)

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(14)
        return page, layout

    def _heading_block(self, layout: QVBoxLayout, title: str, desc: str | None = None) -> None:
        label = QLabel(title)
        label.setObjectName("CardTitle")
        label.setStyleSheet("font-size: 14pt; font-weight: 750;")
        layout.addWidget(label)
        if desc:
            d = QLabel(desc)
            d.setObjectName("Muted")
            d.setWordWrap(True)
            layout.addWidget(d)

    def _scroll_page(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _body_box(self, parent_layout: QVBoxLayout) -> QWidget:
        body = QWidget()
        parent_layout.addWidget(body, 1)
        return body

    def _add_tool_grid(self, category: str = "all", favorites_only: bool = False) -> QWidget:
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(2, 2, 2, 2)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        favs = set(self.settings.get("favorites", []))
        selected = []
        q = self.query.casefold().strip()
        for a in ACTIONS:
            if category != "all" and a["cat"] != category:
                continue
            if favorites_only and a["id"] not in favs:
                continue
            searchable = " ".join([a["title"], a["en"], a["fr"], a["desc"], a["desc_en"], a["cmd"]]).casefold()
            if q and q not in searchable:
                continue
            selected.append(a)
        if not selected:
            empty = QLabel(self.tr("no_results"))
            empty.setObjectName("Muted")
            grid.addWidget(empty, 0, 0)
        for index, action in enumerate(selected):
            card = ToolCard(action, self.lang, self.theme, action["id"] in favs)
            card.run_requested.connect(self.run_action_by_id)
            card.favorite_requested.connect(self.toggle_favorite)
            card.copy_requested.connect(self.copy_action_by_id)
            grid.addWidget(card, index // 2, index % 2)
            self._fade_in(card, 35 * index)
        return content

    def _fade_in(self, widget: QWidget, delay: int = 0) -> None:
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Keep a reference on the widget until animation finishes.
        widget._winkit_anim = anim  # type: ignore[attr-defined]
        QTimer.singleShot(delay, anim.start)

    # ----------------------- Page builders -----------------------
    def build_dashboard(self) -> QWidget:
        page, layout = self._page()
        hero = QFrame(); hero.setObjectName("Card")
        hl = QHBoxLayout(hero); hl.setContentsMargins(22, 20, 22, 20)
        text_col = QVBoxLayout()
        title = QLabel(self.tr("welcome")); title.setStyleSheet("font-size: 22pt; font-weight: 800;")
        sub = QLabel(self.tr("welcome_sub")); sub.setObjectName("Muted"); sub.setWordWrap(True)
        text_col.addWidget(title); text_col.addWidget(sub)
        hl.addLayout(text_col, 1)
        badge = QLabel("✦  WIN / KIT")
        badge.setStyleSheet(f"background:{self.theme['card2']};color:{self.theme['accent']};padding:16px;border-radius:15px;font-size:15pt;font-weight:800;")
        hl.addWidget(badge)
        layout.addWidget(hero)
        metric_row = QGridLayout()
        for i, key in enumerate(["cpu", "ram", "disk", "uptime"]):
            card = MetricCard(self.tr(key))
            self.metric_cards[key] = card
            metric_row.addWidget(card, 0, i)
        layout.addLayout(metric_row)
        self._heading_block(layout, self.tr("quick_actions"), self.tr("dashboard_hint"))
        quick = QGridLayout(); quick.setHorizontalSpacing(10); quick.setVerticalSpacing(10)
        quick_items = [("repair", "🩺"), ("software", "📦"), ("hardware", "◉"), ("disk", "💽"), ("report", "▤"), ("tools", "⌘")]
        for idx, (target, icon) in enumerate(quick_items):
            b = QPushButton(f"{icon}   {self.tr(target)}")
            b.setMinimumHeight(56)
            b.clicked.connect(lambda checked=False, k=target: self.navigate(k))
            quick.addWidget(b, idx // 3, idx % 3)
        layout.addLayout(quick)
        self._heading_block(layout, self.tr("recent"))
        self.dashboard_recent = QLabel("")
        self.dashboard_recent.setObjectName("Muted")
        self.dashboard_recent.setWordWrap(True)
        layout.addWidget(self.dashboard_recent)
        layout.addStretch(1)
        return page

    def build_tools(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("all_tools"), self.tr("quick_search_tip"))
        filter_row = QHBoxLayout()
        filter_label = QLabel(CATEGORY_TRANSLATIONS[self.lang]["all"])
        filter_label.setObjectName("Muted")
        self.category_combo = QComboBox()
        for key in CATEGORY_KEYS:
            self.category_combo.addItem(CATEGORY_TRANSLATIONS[self.lang][key], key)
        self.category_combo.setCurrentIndex(max(0, self.category_combo.findData(self.current_category)))
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.category_combo, 0)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)
        self.tools_scroll = self._scroll_page(self._add_tool_grid(self.current_category))
        # The scroll content is re-created on navigation / search.
        layout.addWidget(self.tools_scroll, 1)
        return page

    def build_repair(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("fix_title"), self.tr("fix_desc"))
        card = QFrame(); card.setObjectName("Card")
        cl = QVBoxLayout(card)
        title = QLabel(self.tr("network_test")); title.setObjectName("CardTitle")
        desc = QLabel(self.tr("network_test_desc")); desc.setObjectName("Muted")
        desc.setWordWrap(True)
        btn = QPushButton("🔎   " + self.tr("network_test")); btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self.run_network_diagnostics)
        cl.addWidget(title); cl.addWidget(desc); cl.addWidget(btn)
        layout.addWidget(card)
        action_grid = self._add_tool_grid("repair")
        layout.addWidget(self._scroll_page(action_grid), 1)
        self.repair_output = QPlainTextEdit(); self.repair_output.setReadOnly(True); self.repair_output.setMaximumHeight(170)
        self.repair_output.setPlaceholderText(self.tr("ready"))
        layout.addWidget(self.repair_output)
        return page

    def build_performance(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("performance_title"), self.tr("performance_desc"))
        preset = QFrame(); preset.setObjectName("Card")
        pl = QVBoxLayout(preset)
        title = QLabel(self.tr("low_end")); title.setObjectName("CardTitle")
        desc = QLabel(self.tr("low_end_desc")); desc.setObjectName("Muted"); desc.setWordWrap(True)
        btnrow = QHBoxLayout()
        apply_btn = QPushButton("⚡   " + self.tr("low_end")); apply_btn.setObjectName("PrimaryButton")
        apply_btn.clicked.connect(self.apply_low_end_preset)
        restore_btn = QPushButton("↩   " + self.tr("restore")); restore_btn.clicked.connect(self.restore_performance)
        btnrow.addWidget(apply_btn); btnrow.addWidget(restore_btn)
        pl.addWidget(title); pl.addWidget(desc); pl.addLayout(btnrow)
        layout.addWidget(preset)
        links = QGridLayout()
        for idx, (label, uri) in enumerate([(self.tr("gaming"),"ms-settings:gaming-gamemode"),(self.tr("battery"),"ms-settings:powersleep"),(self.tr("startup"),"ms-settings:startupapps")]):
            b = QPushButton(label); b.setMinimumHeight(55)
            b.clicked.connect(lambda checked=False, u=uri: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(b, 0, idx)
        layout.addLayout(links)
        note = QLabel(self.tr("theme_note")); note.setObjectName("Muted")
        layout.addWidget(note)
        more = self._add_tool_grid("performance")
        layout.addWidget(self._scroll_page(more), 1)
        return page

    def build_hardware(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("hardware"), self.tr("dashboard_hint"))
        grid = QGridLayout()
        self.hardware_metrics: dict[str, MetricCard] = {}
        for i, key in enumerate(["cpu", "ram", "disk", "uptime"]):
            card = MetricCard(self.tr(key)); self.hardware_metrics[key] = card
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)
        self._heading_block(layout, self.tr("processes"))
        self.process_output = QPlainTextEdit(); self.process_output.setReadOnly(True); self.process_output.setMaximumHeight(240)
        layout.addWidget(self.process_output)
        self.gpu_note = QLabel(self.tr("gpu_unavailable")); self.gpu_note.setObjectName("Muted"); self.gpu_note.setWordWrap(True)
        layout.addWidget(self.gpu_note)
        refresh = QPushButton("↻   " + self.tr("refresh")); refresh.clicked.connect(self.refresh_metrics)
        layout.addWidget(refresh, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        return page

    def build_software(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("software_title"), self.tr("software_desc"))
        card = QFrame(); card.setObjectName("Card")
        cl = QVBoxLayout(card)
        row = QHBoxLayout()
        for label, callback, primary in [
            (self.tr("installed_apps"), lambda: self.run_winget("list"), False),
            (self.tr("check_updates"), lambda: self.run_winget("upgrade"), True),
            (self.tr("export_apps"), self.export_app_list, False),
            (self.tr("import_apps"), self.import_app_list, False),
        ]:
            b = QPushButton(label); b.setObjectName("PrimaryButton" if primary else "SecondaryButton")
            b.clicked.connect(callback); row.addWidget(b)
        cl.addLayout(row)
        update_btn = QPushButton("⬆   " + self.tr("update_all")); update_btn.setObjectName("PrimaryButton")
        update_btn.clicked.connect(self.update_all_apps)
        cl.addWidget(update_btn)
        layout.addWidget(card)
        self.software_output = QPlainTextEdit(); self.software_output.setReadOnly(True)
        self.software_output.setPlaceholderText(self.tr("ready"))
        layout.addWidget(self.software_output, 1)
        note = QLabel(self.tr("software_note"))
        note.setObjectName("Muted"); note.setWordWrap(True)
        layout.addWidget(note)
        return page

    def build_disk(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("disk_title"), self.tr("disk_desc"))
        row = QHBoxLayout()
        self.folder_input = QLineEdit(); self.folder_input.setPlaceholderText(self.tr("disk_empty"))
        choose = QPushButton(self.tr("choose_folder")); choose.clicked.connect(self.choose_disk_folder)
        scan = QPushButton(self.tr("scan_folder")); scan.setObjectName("PrimaryButton"); scan.clicked.connect(self.start_disk_scan)
        row.addWidget(self.folder_input, 1); row.addWidget(choose); row.addWidget(scan)
        layout.addLayout(row)
        self.disk_output = QPlainTextEdit(); self.disk_output.setReadOnly(True); self.disk_output.setPlaceholderText(self.tr("disk_empty"))
        layout.addWidget(self.disk_output, 1)
        hash_card = QFrame(); hash_card.setObjectName("Card")
        hcl = QVBoxLayout(hash_card)
        htitle = QLabel(self.tr("hash_title")); htitle.setObjectName("CardTitle")
        hdesc = QLabel(self.tr("hash_desc")); hdesc.setObjectName("Muted")
        hrow = QHBoxLayout()
        choose_file = QPushButton(self.tr("choose_file")); choose_file.clicked.connect(self.calculate_hash)
        self.hash_output = QLineEdit(); self.hash_output.setReadOnly(True); self.hash_output.setPlaceholderText("SHA-256")
        hrow.addWidget(self.hash_output, 1); hrow.addWidget(choose_file)
        hcl.addWidget(htitle); hcl.addWidget(hdesc); hcl.addLayout(hrow)
        layout.addWidget(hash_card)
        return page

    def build_report(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("report_title"), self.tr("report_desc"))
        card = QFrame(); card.setObjectName("Card")
        cl = QVBoxLayout(card)
        info = QLabel(self.tr("report_privacy_note"))
        info.setObjectName("Muted"); info.setWordWrap(True)
        btn = QPushButton("▤   " + self.tr("generate_report")); btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self.generate_report)
        cl.addWidget(info); cl.addWidget(btn)
        layout.addWidget(card)
        self.report_status = QLabel(""); self.report_status.setObjectName("Muted")
        layout.addWidget(self.report_status)
        layout.addStretch(1)
        return page

    def build_favorites(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("favorites"))
        self.favorites_scroll = self._scroll_page(self._add_tool_grid(favorites_only=True))
        layout.addWidget(self.favorites_scroll, 1)
        return page

    def build_activity(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("activity"))
        self.activity_output = QPlainTextEdit(); self.activity_output.setReadOnly(True)
        layout.addWidget(self.activity_output, 1)
        clear = QPushButton("⌫   " + ("مسح السجل" if self.lang == "ar" else "Clear history" if self.lang == "en" else "Effacer l'historique"))
        clear.clicked.connect(self.clear_activity)
        layout.addWidget(clear, 0, Qt.AlignmentFlag.AlignLeft)
        return page

    def build_settings(self) -> QWidget:
        page, layout = self._page()
        self._heading_block(layout, self.tr("settings_title"), self.tr("settings_desc"))
        card = QFrame(); card.setObjectName("Card")
        cl = QVBoxLayout(card)
        theme_title = QLabel(self.tr("theme")); theme_title.setObjectName("CardTitle")
        theme_row = QHBoxLayout()
        self.settings_theme = QComboBox()
        self.settings_theme.addItem(self.tr("theme_dark"), "dark")
        self.settings_theme.addItem(self.tr("theme_light"), "light")
        self.settings_theme.addItem(self.tr("theme_midnight"), "midnight")
        self.settings_theme.addItem(self.tr("theme_graphite"), "graphite")
        self.settings_theme.setCurrentIndex(max(0, self.settings_theme.findData(self.theme_name)))
        self.settings_theme.currentIndexChanged.connect(lambda: self.change_theme(self.settings_theme.currentData()))
        theme_row.addWidget(self.settings_theme, 1)
        cl.addWidget(theme_title); cl.addLayout(theme_row)
        lang_title = QLabel(self.tr("language")); lang_title.setObjectName("CardTitle")
        self.settings_language = QComboBox()
        self.settings_language.addItem("العربية", "ar"); self.settings_language.addItem("English", "en"); self.settings_language.addItem("Français", "fr")
        self.settings_language.setCurrentIndex(["ar","en","fr"].index(self.lang))
        self.settings_language.currentIndexChanged.connect(lambda: self.change_language(self.settings_language.currentData()))
        cl.addWidget(lang_title); cl.addWidget(self.settings_language)
        cl.addSpacing(10)
        note = QLabel(self.tr("theme_note") + "\n" + self.tr("appearance_note")); note.setObjectName("Muted"); note.setWordWrap(True)
        cl.addWidget(note)
        layout.addWidget(card)
        safety = QLabel(self.tr("safety_note"))
        safety.setObjectName("Muted"); safety.setWordWrap(True)
        layout.addWidget(safety)
        layout.addStretch(1)
        return page

    # ----------------------- Navigation and refresh -----------------------
    def navigate(self, key: str, animate: bool = True) -> None:
        if key not in self.page_widgets:
            key = "dashboard"
        self.current_page = key
        self.page_heading.setText(self.tr(key) if key in TEXTS[self.lang] else key.title())
        if animate:
            self.pages.show_page(self.page_widgets[key])
        else:
            self.pages.setCurrentWidget(self.page_widgets[key])
        for nav_key, button in self.nav_buttons.items():
            button.setProperty("active", nav_key == key)
            button.style().unpolish(button); button.style().polish(button)
        self.refresh_page_data(key)

    def refresh_page_data(self, key: str) -> None:
        if key == "dashboard":
            recent = self.settings.get("recent", [])[:5]
            if recent:
                parts = []
                for item in recent:
                    action = next((a for a in ACTIONS if a["id"] == item.get("id")), None)
                    name = action["title"] if action and self.lang == "ar" else (action.get(self.lang, action.get("en")) if action else item.get("id"))
                    parts.append(f"• {name} · {item.get('time','')}")
                self.dashboard_recent.setText("\n".join(parts))
            else:
                self.dashboard_recent.setText(self.tr("activity_empty"))
        elif key == "tools":
            old = self.tools_scroll.widget()
            self.tools_scroll.setWidget(self._add_tool_grid(self.current_category))
            if old: old.deleteLater()
        elif key == "favorites":
            old = self.favorites_scroll.widget()
            self.favorites_scroll.setWidget(self._add_tool_grid(favorites_only=True))
            if old: old.deleteLater()
        elif key == "activity":
            history = self.settings.get("recent", [])
            lines = []
            for item in history:
                action = next((a for a in ACTIONS if a["id"] == item.get("id")), None)
                name = action["title"] if action and self.lang == "ar" else (action.get(self.lang, action.get("en")) if action else item.get("id"))
                lines.append(f"{item.get('time','')}  |  {name}  |  {item.get('status','')}")
            self.activity_output.setPlainText("\n".join(lines) if lines else self.tr("activity_empty"))

    def on_search_changed(self, value: str) -> None:
        self.query = value
        if self.current_page not in ("tools", "favorites"):
            self.current_category = "all"
            self.navigate("tools")
        else:
            self.refresh_page_data(self.current_page)

    def on_category_changed(self, _index: int) -> None:
        if hasattr(self, "category_combo") and self.category_combo.currentData():
            self.current_category = self.category_combo.currentData()
            if self.current_page == "tools":
                self.refresh_page_data("tools")

    def on_theme_changed(self, _index: int) -> None:
        if self.theme_combo.currentData():
            self.change_theme(self.theme_combo.currentData())

    def on_language_changed(self, _index: int) -> None:
        if self.lang_combo.currentData() and self.lang_combo.currentData() != self.lang:
            self.change_language(self.lang_combo.currentData())

    def change_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.settings["theme"] = theme_name
        write_json(SETTINGS_PATH, self.settings)
        # Rebuild to recolor custom card labels and theme-dependent surfaces.
        self._build_ui(); self._apply_theme()
        self.status_label.setText(self.tr("done"))

    def change_language(self, language: str) -> None:
        if language not in TEXTS or language == self.lang:
            return
        self.lang = language
        self.settings["language"] = language
        write_json(SETTINGS_PATH, self.settings)
        self._build_ui(); self._apply_theme()

    def refresh_metrics(self) -> None:
        if psutil is None:
            for key, card in self.metric_cards.items():
                card.update_value(self.tr(key), 0, "N/A")
            if hasattr(self, "hardware_metrics"):
                self.process_output.setPlainText(self.tr("metrics_unavailable"))
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\") if is_windows() else psutil.disk_usage("/")
            uptime_seconds = int(time.time() - psutil.boot_time())
            uptime = f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h"
            values = {"cpu":(cpu, f"{cpu:.0f}%"), "ram":(mem.percent, f"{mem.percent:.0f}% · {mem.used/(1024**3):.1f}/{mem.total/(1024**3):.1f} GB"), "disk":(disk.percent, f"{disk.percent:.0f}% · {disk.free/(1024**3):.0f} GB free"), "uptime":(0, uptime)}
            for key, (pct, display) in values.items():
                if key in self.metric_cards:
                    self.metric_cards[key].update_value(self.tr("disk_usage") if key == "disk" else self.tr(key), pct, display)
                if hasattr(self, "hardware_metrics") and key in self.hardware_metrics:
                    self.hardware_metrics[key].update_value(self.tr("disk_usage") if key == "disk" else self.tr(key), pct, display)
            if self.current_page == "hardware" and hasattr(self, "process_output"):
                try:
                    rows = sorted(psutil.process_iter(["name", "memory_info"]), key=lambda p: (p.info.get("memory_info").rss if p.info.get("memory_info") else 0), reverse=True)[:8]
                    lines = [f"{p.info.get('name') or 'Unknown'}  ·  {(p.info.get('memory_info').rss/(1024**2)):.0f} MB" for p in rows if p.info.get("memory_info")]
                    self.process_output.setPlainText("\n".join(lines))
                except (psutil.Error, OSError):
                    pass
        except Exception as exc:
            if hasattr(self, "status_label"):
                self.status_label.setText(f"Metrics unavailable: {exc}")

    # ----------------------- Actions -----------------------
    def get_action(self, action_id: str) -> dict[str, Any] | None:
        return next((a for a in ACTIONS if a["id"] == action_id), None)

    def run_action_by_id(self, action_id: str) -> None:
        action = self.get_action(action_id)
        if not action:
            return
        if not is_windows():
            QMessageBox.warning(self, self.tr("error"), self.tr("windows_only")); return
        if action.get("confirm"):
            name = action["title"] if self.lang == "ar" else action.get(self.lang, action["en"])
            desc = action["desc"] if self.lang == "ar" else action.get("desc_" + self.lang, action["desc_en"])
            extra = "\n\n" + (self.tr("danger_note") if action["risk"] == "high" else self.tr("admin_note") if action["kind"] == "admin" else "")
            if QMessageBox.warning(self, self.tr("confirm"), f"{name}\n\n{desc}{extra}", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
        self.status_label.setText(self.tr("working"))
        add_activity(self.settings, action_id, "started")
        if action["kind"] in ("temp", "dark_theme", "light_theme", "restore_theme"):
            self.run_worker(lambda: launch_action(action, self.lang), lambda result: self.action_complete(action, result), self.action_failed)
        else:
            try:
                result = launch_action(action, self.lang)
                self.action_complete(action, result)
            except Exception as exc:
                self.action_failed(str(exc))

    def action_complete(self, action: dict[str, Any], message: str) -> None:
        self.status_label.setText(message)
        add_activity(self.settings, action["id"], "completed")
        self.refresh_page_data("dashboard")
        QMessageBox.information(self, "WinKit", message)

    def action_failed(self, message: str) -> None:
        self.status_label.setText(f"{self.tr('error')}: {message}")
        QMessageBox.critical(self, self.tr("error"), message)

    def copy_action_by_id(self, action_id: str) -> None:
        action = self.get_action(action_id)
        if action:
            QApplication.clipboard().setText(action["cmd"])
            self.status_label.setText(self.tr("copy_done"))

    def toggle_favorite(self, action_id: str) -> None:
        favorites = set(self.settings.get("favorites", []))
        if action_id in favorites:
            favorites.remove(action_id)
        else:
            favorites.add(action_id)
        self.settings["favorites"] = sorted(favorites)
        write_json(SETTINGS_PATH, self.settings)
        self.refresh_page_data(self.current_page)

    def run_worker(self, fn: Callable[[], Any], on_done: Callable[[Any], None], on_error: Callable[[str], None]) -> None:
        worker = Worker(fn)
        worker.signals.finished.connect(on_done)
        worker.signals.error.connect(on_error)
        self.thread_pool.start(worker)

    # ----------------------- Performance preset -----------------------
    def apply_low_end_preset(self) -> None:
        if not is_windows():
            QMessageBox.warning(self, self.tr("error"), self.tr("windows_only")); return
        prompt = self.tr("low_end_desc") + "\n\n" + self.tr("theme_note")
        if QMessageBox.question(self, self.tr("confirm"), prompt) != QMessageBox.StandardButton.Yes:
            return
        def work():
            apply_registry_group("performance", PERFORMANCE_VALUES)
            return self.tr("low_end_applied")
        self.status_label.setText(self.tr("working"))
        self.run_worker(work, lambda msg: self._preset_done(msg), self.action_failed)

    def _preset_done(self, msg: str) -> None:
        self.status_label.setText(msg); QMessageBox.information(self, "WinKit", msg)

    def restore_performance(self) -> None:
        if QMessageBox.question(self, self.tr("confirm"), self.tr("restore")) != QMessageBox.StandardButton.Yes:
            return
        self.run_worker(lambda: restore_registry_group("performance"), lambda count: self._preset_done(self.tr("restore_performance_done").format(count=count)), self.action_failed)

    # ----------------------- Smart Fix -----------------------
    def run_network_diagnostics(self) -> None:
        self.repair_output.setPlainText(self.tr("scan_running"))
        self.run_worker(network_diagnostics, self._network_done, self.action_failed)

    def _network_done(self, result: str) -> None:
        self.repair_output.setPlainText(result)
        self.status_label.setText(self.tr("scan_complete"))

    # ----------------------- Software Center -----------------------
    def run_winget(self, command: str) -> None:
        if not is_windows():
            QMessageBox.warning(self, self.tr("error"), self.tr("windows_only")); return
        if not shutil.which("winget"):
            QMessageBox.warning(self, self.tr("error"), self.tr("winget_missing")); return
        self.software_output.setPlainText(self.tr("working"))
        def work():
            proc = subprocess.run(["winget", *command.split()], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            return (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "") + f"\n\nExit code: {proc.returncode}"
        self.run_worker(work, lambda output: self._winget_output_ready(command, output), lambda e: self.software_output.setPlainText(f"{self.tr('error')}: {e}"))

    def _winget_output_ready(self, command: str, output: str) -> None:
        self.software_output.setPlainText(output)
        if command == "upgrade":
            self.software_update_previewed = "Exit code: 0" in output

    def import_app_list(self) -> None:
        if not is_windows() or not shutil.which("winget"):
            QMessageBox.warning(self, self.tr("error"), self.tr("winget_missing")); return
        filename, _ = QFileDialog.getOpenFileName(self, self.tr("import_apps"), str(Path.home()), "JSON (*.json)")
        if not filename:
            return
        try:
            manifest = json.loads(Path(filename).read_text(encoding="utf-8"))
            packages = manifest.get("Packages") if isinstance(manifest, dict) else None
            if not isinstance(packages, list) or not packages:
                raise ValueError("The selected file does not look like a WinGet export with a non-empty Packages list.")
            ids = [str(p.get("PackageIdentifier", "")) for p in packages if isinstance(p, dict) and p.get("PackageIdentifier")]
            if not ids:
                raise ValueError("No package identifiers were found in this WinGet export.")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            QMessageBox.warning(self, self.tr("error"), str(exc)); return
        preview = "\n".join(ids[:8])
        more = f"\n... and {len(ids)-8} more" if len(ids) > 8 else ""
        prompt = (f"سيحاول WinGet تثبيت {len(ids)} برنامجًا من الملف التالي:\n{preview}{more}\n\nراجع الملف ومصادر الحزم قبل الاستمرار. هل تريد المتابعة؟" if self.lang == "ar" else f"WinGet will attempt to install {len(ids)} packages from this file:\n{preview}{more}\n\nReview the manifest and package sources before continuing. Proceed?")
        if QMessageBox.warning(self, self.tr("confirm"), prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            command = "winget import --import-file " + subprocess.list2cmdline([filename]) + " --accept-source-agreements"
            subprocess.Popen(["cmd.exe", "/k", command], creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            self.software_output.setPlainText(f"{command}\nA separate console window was opened.")
        except Exception as exc:
            self.software_output.setPlainText(f"{self.tr('error')}: {exc}")

    def update_all_apps(self) -> None:
        if not is_windows() or not shutil.which("winget"):
            QMessageBox.warning(self, self.tr("error"), self.tr("winget_missing")); return
        if not self.software_update_previewed:
            QMessageBox.information(self, self.tr("confirm"), self.tr("update_reminder"))
            return
        if QMessageBox.warning(self, self.tr("confirm"), self.tr("update_warning"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            subprocess.Popen(["cmd.exe", "/k", "winget upgrade --all"], creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            self.software_update_previewed = False
            self.software_output.setPlainText("winget upgrade --all\nA separate console window was opened.")
        except Exception as exc:
            self.software_output.setPlainText(f"{self.tr('error')}: {exc}")

    def export_app_list(self) -> None:
        if not is_windows() or not shutil.which("winget"):
            QMessageBox.warning(self, self.tr("error"), self.tr("winget_missing")); return
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("export_apps"), str(Path.home() / "WinKit-apps.json"), "JSON (*.json)")
        if not filename:
            return
        def work():
            proc = subprocess.run(["winget", "export", "--output", filename, "--include-versions"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or f"WinGet exit code {proc.returncode}")
            return filename
        self.run_worker(work, lambda path: QMessageBox.information(self, "WinKit", f"{self.tr('report_saved')}\n{path}"), self.action_failed)

    # ----------------------- Disk tools -----------------------
    def choose_disk_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self.tr("choose_folder"), str(Path.home()))
        if folder:
            self.folder_input.setText(folder)

    def start_disk_scan(self) -> None:
        folder = Path(self.folder_input.text().strip()).expanduser()
        if not folder.is_dir():
            QMessageBox.warning(self, self.tr("error"), self.tr("disk_empty")); return
        self.disk_output.setPlainText(self.tr("scanning"))
        self.run_worker(lambda: scan_folder(folder), self._disk_scan_done, self.action_failed)

    def _disk_scan_done(self, result: dict[str, Any]) -> None:
        total_gb = result["total"] / (1024**3)
        lines = [self.tr("disk_files_scanned").format(count=result['scanned']), self.tr("disk_total").format(size=total_gb), "", self.tr("largest_files")]
        for size, path in result["largest"]:
            lines.append(f"{size/(1024**2):9.1f} MB  |  {path}")
        lines.append("\n" + self.tr("largest_types"))
        for ext, size in result["extensions"]:
            lines.append(f"{ext:18} {size/(1024**2):.1f} MB")
        if result["errors"]:
            lines.append("\n" + self.tr("skipped_files").format(count=result['errors']))
        if result["limited"]:
            lines.append("\n" + self.tr("scan_limit"))
        self.disk_output.setPlainText("\n".join(lines))

    def calculate_hash(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, self.tr("choose_file"), str(Path.home()))
        if not filename:
            return
        self.hash_output.setText(self.tr("working"))
        def work():
            digest = hashlib.sha256()
            with open(filename, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()
        self.run_worker(work, lambda value: self.hash_output.setText(value), self.action_failed)

    # ----------------------- Reports and history -----------------------
    def generate_report(self) -> None:
        default = Path.home() / "WinKit-System-Report.html"
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("generate_report"), str(default), "HTML (*.html)")
        if not filename:
            return
        self.report_status.setText(self.tr("working"))
        def work():
            report = make_system_report()
            Path(filename).write_text(report, encoding="utf-8")
            return filename
        self.run_worker(work, lambda path: self._report_done(path), self.action_failed)

    def _report_done(self, path: str) -> None:
        self.report_status.setText(f"{self.tr('report_saved')} {path}")
        QMessageBox.information(self, "WinKit", f"{self.tr('report_saved')}\n{path}")

    def clear_activity(self) -> None:
        if QMessageBox.question(self, self.tr("confirm"), self.tr("clear_history_confirm")) == QMessageBox.StandardButton.Yes:
            self.settings["recent"] = []
            write_json(SETTINGS_PATH, self.settings)
            self.refresh_page_data("activity")
            self.refresh_page_data("dashboard")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("WinKit")
    app.setFont(QFont("Segoe UI", 10))
    window = WinKitWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
