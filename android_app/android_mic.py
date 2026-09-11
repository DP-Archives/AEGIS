"""Android speech recognition via pyjnius — used by main.py on the phone."""
from jnius import autoclass, PythonJavaClass, java_method

PythonActivity = autoclass("org.kivy.python.PythonActivity")
Activity = autoclass("android.os.AsyncTask")
RecognizerIntent = autoclass("android.speech.RecognizerIntent")
Intent = autoclass("android.content.Intent")
RManager = autoclass("android.speech.SpeechRecognizer")
RESULT_OK = -1  # Activity.RESULT_OK

def listen(on_result, on_error, language="en-US"):
    """Fire the Android speech dialog; call callbacks from the speech thread."""
    activity = PythonActivity.mActivity

    def _run():
        try:
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                             RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, False)

            class _Listener(PythonJavaClass):
                __javainterfaces__ = ["android/speech/SpeechRecognizer$Listener"]
                __javacontext__ = "foreground"

                @java_method("(Landroid/speech/SpeechRecognizer;)V")
                def onEndOfSpeech(self, sr):
                    pass

                @java_method("(Landroid/os/Bundle;)V")
                def onResults(self, bundle):
                    try:
                        words = bundle.getStringArrayList(
                            "android.speech.extra.RESULTS")
                        text = words.get(0) if words and words.size() > 0 else ""
                    except Exception:
                        text = ""
                    if text:
                        on_result(text)
                    else:
                        on_error("didn't catch that — try again")

                @java_method("(Landroid/speech/SpeechRecognizer;)V")
                def onError(self, sr):
                    on_error("mic error — try again")

            recognizer = RManager.createSpeechRecognizer(activity)
            recognizer.setRecognitionListener(_Listener())
            recognizer.startListening(intent)
        except Exception as e:
            on_error(str(e))

    # SpeechRecognizer must run on a Looper thread — use the UI thread.
    activity.runOnUiThread(_run)
