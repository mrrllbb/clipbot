from blinker import Namespace


clipboard_update_signal = Namespace().signal('clipboard_update_signal')
clipboard_listener = Namespace().signal('clipboard_listener')