// ==============================================================================
// Legal Metrology Compliance-Assist Engine — Centralized Bilingual i18n System
// Languages: English (en) & Hindi (hi)
// ==============================================================================

const TRANSLATIONS = {
  en: {
    // Navigation & Header
    ministryDept: "Ministry of Consumer Affairs • Legal Metrology Division",
    ministryDeptLong: "Ministry of Consumer Affairs, Food & Public Distribution • Pre-Inspection Screening Portal",
    appTitle: "Legal Metrology Compliance-Assist Engine",
    navScanLabel: "Screen Label",
    navDashboard: "Screening Dashboard",
    navLabelScanner: "Label Scanner",
    navAnalytics: "Analytics Dashboard",
    selectLanguage: "Select Language",

    // Statutory Notices
    statutoryNoticeLabel: "Statutory Notice:",
    statutoryNoticeText: "This is a compliance-assist screening report, not a statutory notice under the Legal Metrology Act, 2009. Official enforcement or seizure is strictly reserved for designated Legal Metrology Officers under Section 15.",
    dashboardStatutoryNotice: "This dashboard displays automated pre-inspection compliance screening records. It does not constitute a statutory enforcement log or notice under Section 15 of the Legal Metrology Act, 2009.",
    privacyNote: "Images are processed locally with the self-hosted PaddleOCR engine. No photos or label data are transmitted to external third-party OCR APIs.",

    // Upload & Camera Card
    inputSectionTitle: "1. Input Product Label",
    inputSectionDesc: "Upload a label image or capture directly with device camera for local PaddleOCR screening.",
    btnUploadImage: "Upload Image",
    btnScanCamera: "Scan with Camera",
    dropzoneClick: "Click to browse",
    dropzoneDrag: "or drag and drop label photo here",
    dropzoneHint: "Supports PNG, JPG, JPEG, WEBP (Max 15MB)",
    btnChangeImage: "Change Image",
    alignCameraPrompt: "Align product label within calibration frame",
    btnSwitchCamera: "Switch Camera",
    btnCapturePhoto: "Capture Photo",
    btnCancel: "Cancel",

    // Presets
    quickPresetsLabel: "Quick Test Presets:",
    presetCompliant: "Standard Compliant Pack",
    presetDualMrp: "Dual MRP Anomaly",
    presetCrunchyBites: "Crunchy Bites (Dual MRP Anomaly)",
    presetNutrition: "Nutrition Panel (Not Exempt)",
    presetNonStdUnit: 'Non-Standard Unit ("gm")',
    presetMissingFields: "Missing Consumer Care",
    presetExemptBulk: "Exempt (30 kg Pack)",
    presetExemptSmall: "Small Non-Tobacco (5g)",
    presetTobaccoSmall: "Small Tobacco (5g - Non-Exempt)",

    // Actions & Scanning States
    btnScanAction: "Scan Label & Check Compliance",
    btnScanningAction: "Calibrating & Screening...",
    scanningTitle: "Scanning & Evaluating Label...",
    scanningDesc: "Running PaddleOCR text extraction and evaluating statutory Legal Metrology rules...",

    // Results Section
    resultsTitle: "2. Screening Results",
    scanRefLabel: "Scan Ref ID:",
    evaluatedOnLabel: "Evaluated on:",
    btnDownloadPdf: "Download PDF Report",
    complianceScoreLabel: "Compliance Score:",
    declarationsPassed: "Mandatory Declarations Passed",
    allMandatoryMet: "All 5 mandatory statutory declarations satisfy Legal Metrology (Packaged Commodities) Rules, 2011 specifications.",
    declarationsMissing: "mandatory declaration(s) are missing, flagged, or non-compliant under Rule 6.",

    // Overall Status Verdicts
    statusCompliant: "COMPLIANT",
    statusCompliantDesc: "All 5 mandatory declarations meet Legal Metrology (Packaged Commodities) Rules, 2011 requirements.",
    statusNonCompliant: "NON-COMPLIANT / ANOMALY DETECTED",
    statusNonCompliantDesc: "One or more mandatory declarations are missing, non-compliant, or have price/unit anomalies.",
    statusExempt: "STATUTORY EXEMPTION APPLIED",
    statusExemptDesc: "Package meets statutory exemption criteria under Rule 3 / Rule 26. Standard retail declaration rules are waived.",
    statusUncertain: "UNCERTAIN — LOW OCR CONFIDENCE",
    statusUncertainDesc: "One or more text fields returned low OCR confidence (< 60%). Physical pre-inspection review is recommended.",

    // Exemption Block
    exemptionTitle: "Statutory Exemption Confirmed",
    exemptionRuleRef: "Rule 3 & Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011",

    // Stamped Seal Badges
    stampPass: "PASS",
    stampFlagged: "FLAGGED",
    stampWarning: "FLAGGED",
    stampFail: "FAIL",
    stampUncertain: "UNCERTAIN",
    stampExempt: "EXEMPT",

    // Field Card Headings & Attributes
    detectedValueLabel: "Detected Value:",
    findingLabel: "Finding:",
    explanationLabel: "Explanation / Guidance:",
    noDeclarationDetected: "No matching declaration detected on label",

    // 5 Mandatory Declarations (Rule 6) Names
    fieldMrpName: "Maximum Retail Price (MRP)",
    fieldMrpRule: "Rule 6(1)(e) — Price declaration including all taxes",
    fieldNetQtyName: "Net Quantity",
    fieldNetQtyRule: "Rule 6(1)(b) — Standard SI units (g, kg, ml, l)",
    fieldMfgDateName: "Date of Manufacture / Packing",
    fieldMfgDateRule: "Rule 6(1)(d) — Month & Year of packing",
    fieldMfgAddressName: "Manufacturer / Packer Name & Address",
    fieldMfgAddressRule: "Rule 6(1)(a) — Complete identification & address",
    fieldConsumerCareName: "Consumer Care Contact Details",
    fieldConsumerCareRule: "Rule 6(1)(f) — Name, address, phone or email",

    // Common Rule Findings / Translation mappings
    dualPricingDetected: "Dual pricing detected — Rule 32(2) prohibits multiple MRP declarations without proper correction procedure.",
    nonStandardUnitDetected: "Non-standard unit detected. Legal Metrology Rules mandate standard SI symbols (g, kg, ml, l).",
    missingFieldGeneric: "Mandatory declaration missing on package label.",
    validFieldGeneric: "Statutory declaration detected and verified compliant with Rule 6.",

    // OCR View
    viewOcrText: "View OCR Text Extraction",
    linesDetected: "lines detected",
    noTextDetected: "(No text detected)",

    // Dashboard Analytics Page
    dashboardTitle: "Packaged Commodity Compliance Analytics",
    dashboardSubtitle: "Real-time aggregate telemetry and historical screening logs from automated label inspections.",
    btnRefreshTelemetry: "Refresh Telemetry",
    btnNewScan: "New Label Scan",

    // 4 Dashboard KPI Cards
    metricTotalLabel: "Total Screenings",
    metricTotalHint: "Cumulative scan count",
    metricCompliantLabel: "Compliant Packages",
    metricCompliantRate: "compliance rate",
    metricNonCompliantLabel: "Non-Compliant / Flagged",
    metricNonCompliantHint: "Missing mandatory fields or anomalies",
    metricExemptLabel: "Statutory Exemptions",
    metricExemptHint: "Rule 3 / Rule 26 exemptions",

    // Charts
    chartBreakdownTitle: "Compliance Ratio Breakdown",
    chartVolumeTitle: "Screening Category Volume",
    chartDistribution: "Distribution",
    chartVolumeMetrics: "Volume Metrics",
    chartPassLabel: "Compliant (Pass)",
    chartFailLabel: "Non-Compliant (Flagged)",
    chartExemptLabel: "Statutory Exempt",
    chartUncertainLabel: "Uncertain (Low OCR)",
    chartNoData: "No Inspection Data Recorded",

    // Table Section
    recentRecordsTitle: "Recent Inspection Records",
    recentRecordsDesc: "Most recent packaged commodity screening logs recorded in Supabase cloud database.",
    showingRecords: "Showing",
    ofRecords: "of",
    recordsLabel: "records",
    searchPlaceholder: "Search by Filename, Scan ID, Finding...",
    filterAll: "All Records",
    filterCompliant: "Compliant (Pass)",
    filterNonCompliant: "Flagged / Non-Compliant",
    filterExempt: "Exempt",

    // Table Columns
    thTimestamp: "Timestamp (IST)",
    thScanId: "Scan Reference ID",
    thFilename: "Filename",
    thVerdict: "Verdict",
    thFieldsVerified: "Fields Verified",
    thFinding: "Screening Finding",

    // Empty State
    emptyTitle: "No Scans Recorded Yet",
    emptyDesc: "Upload and evaluate product label images on the scanner page to view screening logs and analytics here.",
    btnScanNow: "Scan a Product Label Now",

    // Toast Notifications
    toastCameraReady: "Live camera scanner ready",
    toastCameraError: "Camera access unavailable. Switching to file upload.",
    toastPhotoCaptured: "Photo captured from camera",
    toastInvalidImage: "Please upload a valid image file (PNG, JPG, JPEG, WEBP)",
    toastImageSelected: "Selected image:",
    toastPresetLoaded: "Loaded preset:",
    toastScanComplete: "Screening Passed: 100% Compliant",
    toastDualMrpAlert: "Dual pricing anomaly detected (Rule 32)",
    toastFlaggedAlert: "Screening Flagged: Review Rule 6 findings",
    toastExemptApplied: "Statutory Exemption Applied (Rule 3/26)",
    toastPdfExporting: "Generating formal compliance screening PDF...",
    toastPdfSuccess: "Compliance report PDF downloaded successfully",
    toastPdfError: "Could not export PDF report",
    toastRefreshingTelemetry: "Refreshing live telemetry...",
    toastTelemetrySynced: "Dashboard telemetry synchronized",

    // Footer
    footerCopy: "Legal Metrology (Packaged Commodities) Rules, 2011 • Smart India Hackathon PS-26034",
    footerLegal: "Designed for pre-inspection screening assistance • Ministry of Consumer Affairs, Food & Public Distribution"
  },

  hi: {
    // Navigation & Header
    ministryDept: "उपभोक्ता मामले मंत्रालय • विधिक मापविज्ञान प्रभाग",
    ministryDeptLong: "उपभोक्ता मामले, खाद्य एवं सार्वजनिक वितरण मंत्रालय • पूर्व-निरीक्षण स्क्रीनिंग पोर्टल",
    appTitle: "विधिक मापविज्ञान अनुपालन-सहायक इंजन",
    navScanLabel: "लेबल स्कैन करें",
    navDashboard: "स्क्रीनिंग डैशबोर्ड",
    navLabelScanner: "लेबल स्कैनर",
    navAnalytics: "एनालिटिक्स डैशबोर्ड",
    selectLanguage: "भाषा चुनें",

    // Statutory Notices
    statutoryNoticeLabel: "वैधानिक सूचना:",
    statutoryNoticeText: "यह एक अनुपालन-सहायता स्क्रीनिंग रिपोर्ट है, विधिक मापविज्ञान अधिनियम, 2009 के तहत वैधानिक नोटिस नहीं। आधिकारिक प्रवर्तन या जब्ती केवल धारा 15 के तहत नामित विधिक मापविज्ञान अधिकारियों के लिए आरक्षित है।",
    dashboardStatutoryNotice: "यह डैशबोर्ड स्वचालित पूर्व-निरीक्षण स्क्रीनिंग रिकॉर्ड प्रदर्शित करता है। यह विधिक मापविज्ञान अधिनियम, 2009 की धारा 15 के तहत कोई वैधानिक प्रवर्तन लॉग या नोटिस नहीं है।",
    privacyNote: "छवियों को स्थानीय रूप से स्व-होस्ट किए गए PaddleOCR इंजन द्वारा प्रोसेस किया जाता है। कोई भी फोटो या डेटा किसी तीसरे पक्ष के OCR API को नहीं भेजा जाता है।",

    // Upload & Camera Card
    inputSectionTitle: "1. उत्पाद लेबल इनपुट करें",
    inputSectionDesc: "स्थानीय PaddleOCR स्क्रीनिंग के लिए लेबल की छवि अपलोड करें या डिवाइस कैमरे से सीधे कैप्चर करें।",
    btnUploadImage: "छवि अपलोड करें",
    btnScanCamera: "कैमरे से स्कैन करें",
    dropzoneClick: "चुनने के लिए क्लिक करें",
    dropzoneDrag: "या लेबल फोटो यहाँ खींचकर छोड़ें",
    dropzoneHint: "PNG, JPG, JPEG, WEBP समर्थित (अधिकतम 15MB)",
    btnChangeImage: "छवि बदलें",
    alignCameraPrompt: "उत्पाद लेबल को कैलिब्रेशन फ्रेम में संरेखित करें",
    btnSwitchCamera: "कैमरा बदलें",
    btnCapturePhoto: "फोटो खींचें",
    btnCancel: "रद्द करें",

    // Presets
    quickPresetsLabel: "त्वरित परीक्षण प्रीसेट:",
    presetCompliant: "मानक अनुपालन पैक",
    presetDualMrp: "दोहरा MRP विसंगति",
    presetCrunchyBites: "क्रंची बाइट्स (दोहरा MRP)",
    presetNutrition: "पोषण पैनल (गैर-मुक्त)",
    presetNonStdUnit: 'गैर-मानक इकाई ("gm")',
    presetMissingFields: "अनुपलब्ध उपभोक्ता सहायता",
    presetExemptBulk: "छूट प्राप्त (30 किग्रा थोक पैक)",
    presetExemptSmall: "छोटा गैर-तंबाकू पैक (5 ग्राम)",
    presetTobaccoSmall: "छोटा तंबाकू पैक (5 ग्राम - गैर-मुक्त)",

    // Actions & Scanning States
    btnScanAction: "लेबल स्कैन करें और अनुपालन जांचें",
    btnScanningAction: "कैलिब्रेट और स्क्रीन किया जा रहा है...",
    scanningTitle: "लेबल स्कैन और मूल्यांकन जारी है...",
    scanningDesc: "PaddleOCR टेक्स्ट निष्कर्षण और विधिक मापविज्ञान नियमों का मूल्यांकन किया जा रहा है...",

    // Results Section
    resultsTitle: "2. स्क्रीनिंग परिणाम",
    scanRefLabel: "स्कैन संदर्भ ID:",
    evaluatedOnLabel: "मूल्यांकन तिथि:",
    btnDownloadPdf: "PDF रिपोर्ट डाउनलोड करें",
    complianceScoreLabel: "अनुपालन स्कोर:",
    declarationsPassed: "अनिवार्य घोषणाएं सत्यापित",
    allMandatoryMet: "सभी 5 अनिवार्य वैधानिक घोषणाएं विधिक मापविज्ञान (पैकेज्ड कमोडिटीज) नियम, 2011 के विनिर्देशों को पूरा करती हैं।",
    declarationsMissing: "अनिवार्य घोषणाएं नियम 6 के तहत अनुपलब्ध, ध्वजांकित या गैर-अनुपालन हैं।",

    // Overall Status Verdicts
    statusCompliant: "अनुपालन पूर्ण (COMPLIANT)",
    statusCompliantDesc: "सभी 5 अनिवार्य घोषणाएं विधिक मापविज्ञान (पैकेज्ड कमोडिटीज) नियम, 2011 की आवश्यकताओं को पूरा करती हैं।",
    statusNonCompliant: "गैर-अनुपालन / विसंगति पाई गई",
    statusNonCompliantDesc: "एक या अधिक अनिवार्य घोषणाएं अनुपलब्ध हैं, गैर-अनुपालन हैं, या मूल्य/इकाई विसंगतियां हैं।",
    statusExempt: "वैधानिक छूट लागू (EXEMPT)",
    statusExemptDesc: "पैकेज नियम 3 / नियम 26 के तहत वैधानिक छूट मानदंडों को पूरा करता है। मानक खुदरा घोषणा नियम माफ हैं।",
    statusUncertain: "अनिश्चित — निम्न OCR विश्वसनीयता",
    statusUncertainDesc: "एक या अधिक टेक्स्ट फ़ील्ड में निम्न OCR विश्वसनीयता (<60%) मिली है। भौतिक पूर्व-निरीक्षण समीक्षा की सिफारिश की जाती है।",

    // Exemption Block
    exemptionTitle: "वैधानिक छूट की पुष्टि",
    exemptionRuleRef: "नियम 3 और नियम 26, विधिक मापविज्ञान (पैकेज्ड कमोडिटीज) नियम, 2011",

    // Stamped Seal Badges
    stampPass: "सही (PASS)",
    stampFlagged: "जांच आवश्यक",
    stampWarning: "जांच आवश्यक",
    stampFail: "असंगत (FAIL)",
    stampUncertain: "अनिश्चित",
    stampExempt: "छूट प्राप्त",

    // Field Card Headings & Attributes
    detectedValueLabel: "पहचाना गया मान:",
    findingLabel: "जांच निष्कर्ष:",
    explanationLabel: "विवरण / मार्गदर्शन:",
    noDeclarationDetected: "लेबल पर कोई मेल खाती घोषणा नहीं मिली",

    // 5 Mandatory Declarations (Rule 6) Names
    fieldMrpName: "अधिकतम खुदरा मूल्य (MRP)",
    fieldMrpRule: "नियम 6(1)(e) — सभी करों सहित मूल्य घोषणा",
    fieldNetQtyName: "शुद्ध मात्रा (Net Quantity)",
    fieldNetQtyRule: "नियम 6(1)(b) — मानक SI इकाइयाँ (g, kg, ml, l)",
    fieldMfgDateName: "निर्माण / पैकिंग की तिथि",
    fieldMfgDateRule: "नियम 6(1)(d) — पैकिंग का माह और वर्ष",
    fieldMfgAddressName: "निर्माता / पैकर का नाम और पता",
    fieldMfgAddressRule: "नियम 6(1)(a) — पूर्ण पहचान और पता",
    fieldConsumerCareName: "उपभोक्ता सहायता संपर्क विवरण",
    fieldConsumerCareRule: "नियम 6(1)(f) — नाम, पता, फोन या ईमेल",

    // Common Rule Findings / Translation mappings
    dualPricingDetected: "एक से अधिक MRP मूल्य पाए गए — नियम 32(2) के अनुसार उचित सुधार प्रक्रिया के बिना कई MRP घोषणाओं की अनुमति नहीं है।",
    nonStandardUnitDetected: "गैर-मानक इकाई पाई गई। विधिक मापविज्ञान नियम केवल मानक SI प्रतीकों (g, kg, ml, l) को अनिवार्य करते हैं।",
    missingFieldGeneric: "पैकेज लेबल पर अनिवार्य वैधानिक घोषणा अनुपलब्ध है।",
    validFieldGeneric: "वैधानिक घोषणा पाई गई और नियम 6 के अनुरूप सत्यापित की गई।",

    // OCR View
    viewOcrText: "पहचाना गया OCR टेक्स्ट देखें",
    linesDetected: "पंक्तियाँ पहचानी गईं",
    noTextDetected: "(कोई टेक्स्ट नहीं मिला)",

    // Dashboard Analytics Page
    dashboardTitle: "पैकेज्ड वस्तु अनुपालन एनालिटिक्स",
    dashboardSubtitle: "स्वचालित लेबल निरीक्षणों से वास्तविक समय कुल टेलीमेट्री और ऐतिहासिक स्क्रीनिंग लॉग।",
    btnRefreshTelemetry: "टेलीमेट्री रिफ्रेश करें",
    btnNewScan: "नया लेबल स्कैन करें",

    // 4 Dashboard KPI Cards
    metricTotalLabel: "कुल स्क्रीनिंग",
    metricTotalHint: "संचयी स्कैन गणना",
    metricCompliantLabel: "अनुपालित पैकेज",
    metricCompliantRate: "अनुपालन दर",
    metricNonCompliantLabel: "गैर-अनुपालित / ध्वजांकित",
    metricNonCompliantHint: "अनुपलब्ध अनिवार्य फ़ील्ड या विसंगतियां",
    metricExemptLabel: "वैधानिक छूट",
    metricExemptHint: "नियम 3 / नियम 26 छूट",

    // Charts
    chartBreakdownTitle: "अनुपालन अनुपात वितरण",
    chartVolumeTitle: "स्क्रीनिंग श्रेणी वॉल्यूम",
    chartDistribution: "वितरण",
    chartVolumeMetrics: "वॉल्यूम मेट्रिक्स",
    chartPassLabel: "अनुपालित (Pass)",
    chartFailLabel: "गैर-अनुपालित (Flagged)",
    chartExemptLabel: "वैधानिक छूट",
    chartUncertainLabel: "अनिश्चित (निम्न OCR)",
    chartNoData: "कोई निरीक्षण डेटा दर्ज नहीं है",

    // Table Section
    recentRecordsTitle: "हालिया निरीक्षण रिकॉर्ड",
    recentRecordsDesc: "सुपाबेस क्लाउड डेटाबेस में दर्ज नवीनतम पैकेज्ड कमोडिटी स्क्रीनिंग लॉग।",
    showingRecords: "दिखाया जा रहा है",
    ofRecords: "में से",
    recordsLabel: "रिकॉर्ड",
    searchPlaceholder: "फ़ाइल नाम, स्कैन ID, निष्कर्ष द्वारा खोजें...",
    filterAll: "सभी रिकॉर्ड",
    filterCompliant: "अनुपालित (Pass)",
    filterNonCompliant: "ध्वजांकित / गैर-अनुपालित",
    filterExempt: "छूट प्राप्त",

    // Table Columns
    thTimestamp: "समय (IST)",
    thScanId: "स्कैन संदर्भ ID",
    thFilename: "फ़ाइल नाम",
    thVerdict: "निर्णय",
    thFieldsVerified: "सत्यापित फ़ील्ड",
    thFinding: "स्क्रीनिंग निष्कर्ष",

    // Empty State
    emptyTitle: "अभी तक कोई स्कैन दर्ज नहीं है",
    emptyDesc: "यहाँ स्क्रीनिंग लॉग और एनालिटिक्स देखने के लिए स्कैनर पेज पर उत्पाद लेबल छवियां अपलोड और जांचें।",
    btnScanNow: "अब एक उत्पाद लेबल स्कैन करें",

    // Toast Notifications
    toastCameraReady: "लाइव कैमरा स्कैनर तैयार है",
    toastCameraError: "कैमरा उपलब्ध नहीं है। फ़ाइल अपलोड पर स्विच किया जा रहा है।",
    toastPhotoCaptured: "कैमरे से फोटो ली गई",
    toastInvalidImage: "कृपया एक वैध छवि फ़ाइल अपलोड करें (PNG, JPG, JPEG, WEBP)",
    toastImageSelected: "चयनित छवि:",
    toastPresetLoaded: "प्रीसेट लोड किया गया:",
    toastScanComplete: "स्क्रीनिंग सफल: 100% अनुपालित",
    toastDualMrpAlert: "दोहरा MRP विसंगति का पता चला (नियम 32)",
    toastFlaggedAlert: "स्क्रीनिंग ध्वजांकित: नियम 6 निष्कर्षों की समीक्षा करें",
    toastExemptApplied: "वैधानिक छूट लागू (नियम 3/26)",
    toastPdfExporting: "औपचारिक अनुपालन स्क्रीनिंग PDF तैयार की जा रही है...",
    toastPdfSuccess: "अनुपालन रिपोर्ट PDF सफलतापूर्वक डाउनलोड हो गई",
    toastPdfError: "PDF रिपोर्ट निर्यात नहीं की जा सकी",
    toastRefreshingTelemetry: "लाइव टेलीमेट्री रिफ्रेश की जा रही है...",
    toastTelemetrySynced: "डैशबोर्ड टेलीमेट्री सिंक्रनाइज़ हो गई",

    // Footer
    footerCopy: "विधिक मापविज्ञान (पैकेज्ड कमोडिटीज) नियम, 2011 • स्मार्ट इंडिया हैकथॉन PS-26034",
    footerLegal: "पूर्व-निरीक्षण स्क्रीनिंग सहायता के लिए डिज़ाइन किया गया • उपभोक्ता मामले, खाद्य एवं सार्वजनिक वितरण मंत्रालय"
  }
};

const STORAGE_KEY = 'lm_engine_preferred_lang';

// Get current active language ('en' or 'hi')
function getLanguage() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'hi' || saved === 'en') {
    return saved;
  }
  return 'en';
}

// Translate key
function t(key, fallback = '') {
  const lang = getLanguage();
  if (TRANSLATIONS[lang] && TRANSLATIONS[lang][key] !== undefined) {
    return TRANSLATIONS[lang][key];
  }
  if (TRANSLATIONS.en && TRANSLATIONS.en[key] !== undefined) {
    return TRANSLATIONS.en[key];
  }
  return fallback || key;
}

// Set language and update whole page immediately without reload
function setLanguage(lang) {
  if (lang !== 'en' && lang !== 'hi') lang = 'en';
  localStorage.setItem(STORAGE_KEY, lang);

  document.documentElement.lang = lang;

  if (lang === 'hi') {
    document.body.classList.add('lang-hi');
  } else {
    document.body.classList.remove('lang-hi');
  }

  // Update switcher buttons UI
  document.querySelectorAll('.btn-lang').forEach(btn => {
    const btnLang = btn.getAttribute('data-lang');
    if (btnLang === lang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key && TRANSLATIONS[lang] && TRANSLATIONS[lang][key] !== undefined) {
      el.textContent = TRANSLATIONS[lang][key];
    }
  });

  // Update elements with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key && TRANSLATIONS[lang] && TRANSLATIONS[lang][key] !== undefined) {
      el.setAttribute('placeholder', TRANSLATIONS[lang][key]);
    }
  });

  // Update elements with data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    if (key && TRANSLATIONS[lang] && TRANSLATIONS[lang][key] !== undefined) {
      el.setAttribute('title', TRANSLATIONS[lang][key]);
    }
  });

  // Dispatch custom event for reactive JS components
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

// Initialize on page load
function initI18n() {
  const currentLang = getLanguage();
  setLanguage(currentLang);

  // Bind click handlers to language buttons
  document.querySelectorAll('.btn-lang').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetLang = btn.getAttribute('data-lang');
      if (targetLang) {
        setLanguage(targetLang);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', initI18n);
