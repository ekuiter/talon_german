mode: user.german
language: de_DE
-

# idea: allow to directly chain commands
# how about using 'ego' (as in jp 'eigo')?
^(englisch | english)$:
    mode.disable("user.german")
    mode.enable("command")

^german mode$: skip()

<user.satz>: user.dictation_insert(satz)
