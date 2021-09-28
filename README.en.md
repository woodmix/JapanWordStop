# JapanWordStop

When jumping a word with ctrl+right, etc., the Sublime standard jumps all kanji and hiragana at the same time for Japanese strings, etc.<br>
This plugin changes the behavior so that caret stops at the point where character type changes.

### Features

- The stop position can be predicted because it is simply judged by the character type only.
- It works by intercepting standard commands, so you don't need to set any shortcut keys (configurable).
- Therefore, it does not interfere with the exceptional behavior of Sublime when double-clicking.
- The "subtractive" option is also supported.
- Ctrl+D for word selection is also supported.
- Word jumps in ASCII strings basically conform to the Sublime standard, and the Sublime setting "word_separators" is also reflected.<br>
However, stop positions involving symbolic characters (especially commas) will be changed (see below).

### Example of a stop position

Caret stops at the position indicated by "|".<br>
\* Treats hiragana as a suffix that is set with the last character, similar to a space character in ASCII strings.
```
|吾輩|《わがはい|》は|猫である|。|名前はまだ|無い|。|
|どこで|生れたかとんと|見当|《けんとう|》がつかぬ|。|何でも|薄暗いじめじめした|所で|ニャーニャー|泣いていた|事だけは|記憶している|。|
|吾輩はここで|始めて|人間というものを|見た|。|しかもあとで|聞くとそれは|書生という|人間中で|一番獰悪|《どうあく|》な|種族であったそうだ|。|
```

If you do a subword jump (alt+right, alt+left), the hiragana will not be skipped.
```
吾輩|《|わがはい|》|は|猫|である|。|名前|はまだ|無|い|。|
|どこで|生|れたかとんと|見当|《|けんとう|》|がつかぬ|。|何|でも|薄暗|いじめじめした|所|で|ニャーニャー|泣|いていた|事|だけは|記憶|している|。|
|吾輩|はここで|始|めて|人間|というものを|見|た|。|しかもあとで|聞|くとそれは|書生|という|人間中|で|一番獰悪|《|どうあく|》|な|種族|であったそうだ|。|
```

### Differences between the Sublime standard on Ascii strings

Following string as an example...
```
loving_word ENUM('hello', 'world', 'sublime') NOT NULL
```

In the Sublime standard, ctrl+right stops at the following positions. You can see that he has a strong awareness of commas.
```
loving_word| ENUM|('hello|'|,| 'world|'|,| 'sublime|'|)| NOT| NULL|
```
On the other hand, ctrl+left stops at the next positions. Attitudes towards commas are changing.
```
|loving_word |ENUM|(|'|hello', |'|world', |'|sublime') |NOT |NULL
```

After introducing this plugin, ctrl+right will stop at the following positions.<br>
Commas are not singled out and simply stop at the word endings and symbol endings.
```
loving_word| ENUM|('|hello|',| '|world|',| '|sublime|')| NOT| NULL|
```
The same goes for ctrl+left. Simply stop at the word beginning and the symbol beginning.
```
|loving_word |ENUM|('|hello|', |'|world|', |'|sublime|') |NOT |NULL
```

The standard Sublime behavior is not very consistent, so I didn't try to reproduce it.

### Note on mouse dragging

By default, Sublime expands the selection word by word by double-clicking and dragging it without releasing the mouse button.<br>
In this plugin, the behavior of selecting Japanese strings word by word when double-clicking is implemented, but the behavior when dragging is left as Sublime standard. In other words, the Japanese strings are still selected together when dragging.<br>
This is because Sublime's on_hover() event has a very large delay and dragging on the ASCII string makes it feel worse when trying to fix it.
# JapanWordStop

When jumping a word with ctrl+right, etc., the Sublime standard jumps all kanji and hiragana at the same time for Japanese strings, etc.<br>
This plugin changes the behavior so that caret stops at the point where character type changes.

### Features

- The stop position can be predicted because it is simply judged by the character type only.
- It works by intercepting standard commands, so you don't need to set any shortcut keys (configurable).
- It does not interfere with Sublime's behavior when double-clicking. and supports Subtractive such as alt+double-click.
- Word jumps in ASCII strings basically conform to the Sublime standard, and the Sublime setting "word_separators" is also reflected.<br>
However, stop positions involving symbolic characters (especially commas) will be changed (see below).

### Example of a stop position

Caret stops at the position indicated by "|".<br>
\* Treats hiragana as a suffix that is set with the last character, similar to a space character in ASCII strings.
```
|吾輩|《わがはい|》は|猫である|。|名前はまだ|無い|。|
|どこで|生れたかとんと|見当|《けんとう|》がつかぬ|。|何でも|薄暗いじめじめした|所で|ニャーニャー|泣いていた|事だけは|記憶している|。|
|吾輩はここで|始めて|人間というものを|見た|。|しかもあとで|聞くとそれは|書生という|人間中で|一番獰悪|《どうあく|》な|種族であったそうだ|。|
```

If you do a subword jump (alt+right, alt+left), the hiragana will not be skipped.
```
吾輩|《|わがはい|》|は|猫|である|。|名前|はまだ|無|い|。|
|どこで|生|れたかとんと|見当|《|けんとう|》|がつかぬ|。|何|でも|薄暗|いじめじめした|所|で|ニャーニャー|泣|いていた|事|だけは|記憶|している|。|
|吾輩|はここで|始|めて|人間|というものを|見|た|。|しかもあとで|聞|くとそれは|書生|という|人間中|で|一番獰悪|《|どうあく|》|な|種族|であったそうだ|。|
```

### Differences between the Sublime standard on Ascii strings

Following string as an example...
```
loving_word ENUM('hello', 'world', 'sublime') NOT NULL
```

In the Sublime standard, ctrl+right stops at the following positions. You can see that he has a strong awareness of commas.
```
loving_word| ENUM|('hello|'|,| 'world|'|,| 'sublime|'|)| NOT| NULL|
```
On the other hand, ctrl+left stops at the next positions. Attitudes towards commas are changing.
```
|loving_word |ENUM|(|'|hello', |'|world', |'|sublime') |NOT |NULL
```

After introducing this plugin, ctrl+right will stop at the following positions.<br>
Commas are not singled out and simply stop at the word endings and symbol endings.
```
loving_word| ENUM|('|hello|',| '|world|',| '|sublime|')| NOT| NULL|
```
The same goes for ctrl+left. Simply stop at the word beginning and the symbol beginning.
```
|loving_word |ENUM|('|hello|', |'|world|', |'|sublime|') |NOT |NULL
```

The standard Sublime behavior is not very consistent, so I didn't try to reproduce it.

### Note on mouse dragging

By default, Sublime expands the selection word by word by double-clicking and dragging it without releasing the mouse button.<br>
In this plugin, the behavior of selecting Japanese strings word by word when double-clicking is implemented, but the behavior when dragging is left as Sublime standard. In other words, the Japanese strings are still selected together when dragging.<br>
This is because Sublime's on_hover() event has a very large delay and dragging on the ASCII string makes it feel worse when trying to fix it.

### Tidbits on subword jumping

It is a subword jump that stops at an underscore "_", but the behavior differs depending on the letters existing on both sides. <br>
For example "AUTO_INCREMENT" and "auto_increment", sub-word jump from the left end to the right (alt+right) will stop in the next position.
```
AUTO|_|INCREMENT|
```
```
auto|_increment|
```
This comes from the Sublime standard, not from this plugin.
