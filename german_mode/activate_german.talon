language: en_US
-
^(german mode | deutsch)$:
    mode.disable("command")
    mode.enable("user.german")

^english$: skip()

^german <phrase>$:
    user.recognize_momentary_german(phrase)
