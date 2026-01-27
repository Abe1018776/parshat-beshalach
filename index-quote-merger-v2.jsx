import React, { useState, useRef } from 'react';
import { Upload, FileText, ChevronDown, ChevronUp, CheckCircle, Download, BookOpen, Hash, Layers, X } from 'lucide-react';

// Sample data (will be used after upload)
const SAMPLE_DATA = [
  { id: 1, sefer: 'רבינו בחיי', summary: 'הקדמה-כל האברים נמשכים אחר הלב, והקב"ה בוחן לבות בנ"י במדת הבטחון', page: 'א׳', quote: 'שלמה המלך ע״ה יזהיר בכתוב הזה על האדם שיזכך מחשבתו ושיתקן מדות הלב לפי שהלב הוא עקר כל האברים שבגוף, וכל האברים נמשכים אחריו ומשועבדים אליו, והוא כאמצע הגוף מושל עליהם מנהיג אותם ומשפיע כחו בכלם.' },
  { id: 2, sefer: 'רבינו בחיי', summary: 'וכתב-כל מקריהם של ישראל במדבר היה נסיון גמור, כדי שיגדלו נפשם השכלית', page: 'א׳', quote: 'ודע כי כל עניני ישראל ומקריהם במדבר הכל היה נסיון גמור, כדי שיגדלו נפשם השכלית במדרגות הבטחון שהוא שרש האמונה, כדי שיהיו ראוים לקבל התורה.' },
  { id: 3, sefer: 'תורת משה', summary: 'ויאמר ה\'-פרנסה הוא הכל כפי הכנת המקבל, כי עון ממית והזכות מטיב', page: 'ג׳', quote: 'הנה אמרו רבותינו ז״ל שבששת ימי בראשית היו נעשים בכל יום שלשה דברים. ובששי נעשו ששה דברים, וכולם הם שנים עשר, כנגד שנים עשר שבטים.' },
  { id: 4, sefer: 'תורת משה', summary: 'או יאמר-כמו שהמן שהי\' לחם רוחני נתן חיות לגוף גשמי', page: 'ג׳', quote: 'ותחת זאת היה מקום להרפות האדם מן התורה. על כן בא האלהים להסיר זה מלבו, ולנסותו, אם בהסתלק ממנו טענה זו ילך בתורתו.' },
  { id: 5, sefer: 'אור המאיר', summary: 'בפסוק ותקח-כפי ההתעוררת של תחתונים, ככה גורמים פעולות של הקב"ה עליהם', page: 'ח׳', quote: 'כפי ההתעוררת של תחתונים, ככה גורמים פעולות של הקב״ה עליהם, ומרים פעלה בלקחה הת״ף בידה, ולמדה זאת שגם נשים אחריה לקחוה.' },
  { id: 6, sefer: 'נועם אלימלך', summary: 'או יאמר-אם הצדיק מלוה לאדם אזי הוא מקשר אתו', page: 'י״א', quote: 'אם הצדיק מלוה לאדם אזי הוא מקשר אתו, אבל אם האדם שמלוה, הוא איש נעצב וריקן, הוא מכניס בו עצבותו ומפסיקו יותר מקדושתו.' },
  { id: 7, sefer: 'קדושת לוי', summary: 'ויסעו-למה נקרא שמו ים סוף, לפי שהים הוא סוף הארץ', page: 'ט״ו', quote: 'למה נקרא שמו ים סוף, לפי שהים הוא סוף הארץ, והנה כשהקב״ה ברא את העולם ברא אותו יש מאין, וכל מה שברא היה הכל בשביל ישראל.' },
  { id: 8, sefer: 'אורח לחיים', summary: 'ויהי-לא יאמר אדם שא"א לעמוד נגד יצה"ר ולכבוש הרע', page: 'כ״ב', quote: 'לא יאמר אדם שא״א לעמוד נגד יצה״ר ולכבוש הרע, כי הנה בני ישראל היו במצרים משוקעים במ״ט שערי טומאה והיו עובדים ע״ז, ואעפ״כ יצאו משם והגיעו למדרגה עליונה.' },
  { id: 9, sefer: 'מנחם ציון', summary: 'ונקדים לבאר ענין קריעת ים סוף, שלכאורה לא היו צריכים לנס גדול כזה', page: 'כ״ג', quote: 'ונקדים לבאר ענין קריעת ים סוף, שלכאורה לא היו צריכים לנס גדול כזה, שהיה יכול לכלות את המצרים בדרך אחר, אלא שרצה הקב״ה להראות לישראל כח גדולתו.' },
];

export default function IndexQuoteMerger() {
  const [step, setStep] = useState(1);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [expandedEntry, setExpandedEntry] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const clearFile = () => {
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const runParsing = () => {
    setProcessing(true);
    setTimeout(() => {
      // In real implementation, this would parse the uploaded file
      // For now, using sample data
      setResults(SAMPLE_DATA);
      setProcessing(false);
      setStep(3);
    }, 1500);
  };

  // Generate Word-compatible HTML and download as .doc
  const downloadDoc = () => {
    if (!results) return;

    const grouped = results.reduce((acc, entry) => {
      if (!acc[entry.sefer]) acc[entry.sefer] = [];
      acc[entry.sefer].push(entry);
      return acc;
    }, {});

    const html = `
<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
<w:View>Print</w:View>
<w:Zoom>100</w:Zoom>
<w:DoNotOptimizeForBrowser/>
</w:WordDocument>
</xml>
<![endif]-->
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: 'David', 'Times New Roman', serif; font-size: 14pt; direction: rtl; text-align: right; }
  h1 { text-align: center; font-size: 24pt; margin-bottom: 5pt; }
  h2 { text-align: center; font-size: 16pt; color: #666; margin-bottom: 20pt; }
  h3 { text-align: center; font-size: 18pt; margin: 20pt 0 15pt; border-bottom: 1pt solid #999; padding-bottom: 5pt; }
  h4 { font-size: 14pt; margin: 15pt 0 8pt; text-decoration: underline; }
  .entry { margin: 8pt 15pt; line-height: 1.6; }
  .ref { font-weight: bold; font-size: 10pt; vertical-align: super; color: #8B4513; }
  .divider { text-align: center; margin: 25pt 0; color: #999; }
  .footnote { margin: 12pt 0; padding: 10pt; background: #f9f9f9; border-right: 3pt solid #8B4513; }
  .fn-num { font-weight: bold; color: #8B4513; }
  .fn-sefer { font-style: italic; color: #666; }
</style>
</head>
<body>
<h1>מפתח עם ציטוטים מלאים</h1>
<h2>פרשת בשלח</h2>
<div class="divider">═══════════════════════════════════════</div>
<h3>מפתח ענינים</h3>
${Object.entries(grouped).map(([sefer, entries]) => `
<h4>${sefer}</h4>
${entries.map(e => `<div class="entry">${e.summary} <span class="ref">[${e.id}]</span></div>`).join('')}
`).join('')}
<div class="divider">═══════════════════════════════════════</div>
<h3>ציטוטים מלאים</h3>
${results.map(e => `
<div class="footnote">
  <span class="fn-num">[${e.id}]</span> <span class="fn-sefer">(${e.sefer}, עמוד ${e.page})</span><br/>
  ${e.quote}
</div>
`).join('')}
</body>
</html>`;

    const blob = new Blob(['\ufeff' + html], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'מפתח_עם_ציטוטים.doc';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const groupedResults = results?.reduce((acc, entry) => {
    if (!acc[entry.sefer]) acc[entry.sefer] = [];
    acc[entry.sefer].push(entry);
    return acc;
  }, {}) || {};

  return (
    <div dir="rtl" className="min-h-screen bg-gradient-to-br from-stone-100 to-amber-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6 bg-gradient-to-r from-amber-800 to-amber-600 text-white rounded-2xl p-6 shadow-xl">
          <h1 className="text-3xl font-bold mb-2">מפתח לציטוט</h1>
          <p className="text-amber-100">מסמך אחד → מפתח עם הערות שוליים מלאות</p>
        </div>

        {/* Progress */}
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2 bg-white rounded-full px-6 py-3 shadow-lg">
            {[1, 2, 3].map((s) => (
              <React.Fragment key={s}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${step >= s ? 'bg-amber-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                  {s}
                </div>
                {s < 3 && <div className={`w-12 h-1 ${step > s ? 'bg-amber-500' : 'bg-gray-200'}`} />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step 1 - Upload */}
        {step === 1 && (
          <div className="bg-white rounded-2xl p-8 shadow-xl">
            <h2 className="text-xl font-bold text-amber-900 mb-4 flex items-center gap-2">
              <Upload className="w-6 h-6" />
              העלאת מסמך
            </h2>
            
            {/* Hidden file input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".docx,.doc"
              className="hidden"
            />
            
            {/* Drop zone */}
            <div 
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-amber-300 rounded-xl p-8 text-center bg-amber-50 hover:bg-amber-100 hover:border-amber-500 transition-colors cursor-pointer"
            >
              {uploadedFile ? (
                <div className="space-y-4">
                  <CheckCircle className="w-16 h-16 mx-auto text-green-500" />
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-lg font-medium text-green-700">{uploadedFile.name}</span>
                    <button 
                      onClick={(e) => { e.stopPropagation(); clearFile(); }}
                      className="p-1 hover:bg-red-100 rounded-full"
                    >
                      <X className="w-5 h-5 text-red-500" />
                    </button>
                  </div>
                  <p className="text-sm text-gray-500">
                    {(uploadedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <>
                  <FileText className="w-16 h-16 mx-auto text-amber-400 mb-4" />
                  <p className="text-lg font-medium text-amber-800 mb-2">לחץ כאן או גרור קובץ DOCX</p>
                  <p className="text-sm text-amber-600">מסמך עם מפתח בתחילה וציטוטים בהמשך</p>
                </>
              )}
            </div>

            <button 
              onClick={() => setStep(2)} 
              disabled={!uploadedFile}
              className="mt-6 w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-colors"
            >
              {uploadedFile ? 'המשך →' : 'יש להעלות קובץ תחילה'}
            </button>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-amber-900 flex items-center gap-2">
                  <Layers className="w-6 h-6" />
                  מבנה המסמך
                </h2>
                <div className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full">
                  📄 {uploadedFile?.name}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-amber-50 rounded-xl p-4">
                  <h3 className="font-bold text-amber-800 mb-2 flex items-center gap-1">
                    <Hash className="w-4 h-4" />מפתח
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="bg-white rounded p-2">רבינו בחיי...א׳</div>
                    <div className="bg-white rounded p-2">תורת משה...ג׳</div>
                  </div>
                </div>
                <div className="bg-orange-50 rounded-xl p-4">
                  <h3 className="font-bold text-orange-800 mb-2 flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />תוכן
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="bg-white rounded p-2 border-r-4 border-orange-400 font-bold">רבינו בחיי</div>
                    <div className="bg-white rounded p-2 text-gray-500">[ציטוט...]</div>
                  </div>
                </div>
              </div>
            </div>
            <button onClick={runParsing} disabled={processing} className="w-full py-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold rounded-xl shadow-lg disabled:opacity-50">
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  מעבד את {uploadedFile?.name}...
                </span>
              ) : '🔗 הפעל מיפוי'}
            </button>
            <button onClick={() => setStep(1)} className="w-full py-2 text-gray-500 hover:text-gray-700">
              ← חזור לבחירת קובץ
            </button>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && results && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-4 text-center shadow-lg">
                <div className="text-3xl font-bold text-amber-600">{results.length}</div>
                <div className="text-sm text-gray-600">רשומות</div>
              </div>
              <div className="bg-white rounded-xl p-4 text-center shadow-lg">
                <div className="text-3xl font-bold text-green-600">{results.length}</div>
                <div className="text-sm text-gray-600">ציטוטים</div>
              </div>
              <div className="bg-white rounded-xl p-4 text-center shadow-lg">
                <div className="text-3xl font-bold text-orange-600">{Object.keys(groupedResults).length}</div>
                <div className="text-sm text-gray-600">ספרים</div>
              </div>
            </div>

            {/* DOWNLOAD BUTTON */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 text-center shadow-xl">
              <Download className="w-12 h-12 mx-auto text-white mb-3" />
              <h3 className="text-xl font-bold text-white mb-2">הורדת קובץ Word</h3>
              <p className="text-green-100 mb-4">לחץ להורדת מסמך שנפתח ב-Word</p>
              <button
                onClick={downloadDoc}
                className="px-8 py-4 bg-white text-green-700 font-bold rounded-xl shadow-lg hover:shadow-xl hover:bg-green-50 transition-all text-lg"
              >
                📥 הורד מפתח_עם_ציטוטים.doc
              </button>
            </div>

            {/* Results Preview */}
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="bg-gradient-to-r from-amber-700 to-amber-600 p-4">
                <h2 className="text-xl font-bold text-white">תצוגה מקדימה</h2>
              </div>
              <div className="divide-y max-h-72 overflow-y-auto">
                {Object.entries(groupedResults).map(([sefer, entries]) => (
                  <div key={sefer} className="p-4">
                    <h3 className="font-bold text-lg text-amber-900 mb-3 pb-2 border-b-2 border-amber-200">{sefer}</h3>
                    <div className="space-y-2">
                      {entries.map((entry) => (
                        <div key={entry.id} className="bg-amber-50 rounded-lg overflow-hidden">
                          <div
                            className="p-3 cursor-pointer hover:bg-amber-100 flex items-start gap-3"
                            onClick={() => setExpandedEntry(expandedEntry === entry.id ? null : entry.id)}
                          >
                            <span className="w-7 h-7 bg-amber-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">{entry.id}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                                <span className="text-xs px-2 py-0.5 bg-amber-200 rounded">עמוד {entry.page}</span>
                              </div>
                              <p className="text-gray-800 text-sm truncate">{entry.summary}</p>
                            </div>
                            {expandedEntry === entry.id ? <ChevronUp className="w-5 h-5 text-amber-500 flex-shrink-0" /> : <ChevronDown className="w-5 h-5 text-amber-500 flex-shrink-0" />}
                          </div>
                          {expandedEntry === entry.id && (
                            <div className="p-4 bg-white border-t border-amber-200">
                              <div className="text-xs text-amber-600 font-bold mb-2">📜 ציטוט מלא:</div>
                              <p className="text-gray-700 text-sm leading-relaxed bg-amber-50 p-3 rounded border-r-4 border-amber-400">{entry.quote}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button onClick={() => { setStep(1); setResults(null); setUploadedFile(null); }} className="w-full py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium rounded-xl">
              ← התחל מחדש
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
