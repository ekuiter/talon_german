language: en_US
-
^(german [mode] | deutsch)$:
    mode.disable("command")
    mode.enable("user.german")

^(english | ego | pego)$: skip()

^dings <phrase>$:
    user.recognize_momentary_german(phrase)
