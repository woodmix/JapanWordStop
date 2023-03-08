import sublime
import sublime_plugin
import re
import sre_constants


#===========================================================================================================
class WordMoveListener(sublime_plugin.ViewEventListener):
    """
    moveコマンドやdrag_selectコマンドを監視して必要に応じて介入する。
    """

    #-----------------------------------------------------------------------------------------------------------
    def is_applicable(settings):
        """
        設定でインターセプトが無効になっているなら処理しない。
        """
        global intercept
        return intercept

    #-----------------------------------------------------------------------------------------------------------
    def applies_to_primary_view_only():
        """
        複製されたビューでも動作するようにする。
        """
        return False

    #-----------------------------------------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.beforeRegions = None

    #-----------------------------------------------------------------------------------------------------------
    def on_text_command(self, command_name, args):

        # "by":"words" あるいは "by":"word_ends" の move コマンドをオリジナルの word_move_uni コマンドに差し替える。ただし、"native":True の場合を除く。
        if command_name == "move":
            if not args.get("native") and args.get("by") in ["words", "word_ends", "subwords", "subword_ends"]:
                return "word_move_uni", args

        # "by":"words" の drag_select コマンドが発行された場合は、処理直前の選択領域をメンバ変数 beforeRegions で保持しておく。
        # これは、処理された直後に直前の選択状態に戻すため。なぜいったん処理させるかと言うと、ダブルクリックした後そのままマウスを動かしたときの挙動を
        # 有効化するためだ。
        # ※有効化するのは良いが、この挙動における単語選択に介入する方法はない(いや on_hover 使えばできるけど、微妙…)のでそれはデフォルトのままで
        # 良しとする。
        if command_name == "drag_select":
            if not args.get("native") and args.get("by") in ["words", "subwords"]:
                self.beforeRegions = [region for region in self.view.sel()]

        # find_under_expand コマンド(Ctrl+D)で領域が空のRegionがある場合は、word_expand_uni コマンドに差し替える。
        if command_name == "find_under_expand":
            for region in self.view.sel():
                if region.empty():
                    return "word_expand_uni"

    #-----------------------------------------------------------------------------------------------------------
    def on_post_text_command(self, command_name, args):

        # "by":"words" の drag_select コマンドが処理された後、領域を設定し直す。ただし "native":True の場合を除く。
        if command_name == "drag_select":
            if not args.get("native") and args.get("by") in ["words", "subwords"]:

                # このメンバ変数は必ずセットされているはずだが、一応チェックする。
                if self.beforeRegions:

                    # 選択領域を drag_select コマンドが発行された直前の状態に復元する。
                    self.view.sel().clear()
                    self.view.sel().add_all(self.beforeRegions)
                    self.beforeRegions = None;

                    # word_select_uni コマンドに転送する。
                    self.view.run_command("word_select_uni", args)


#===========================================================================================================
class WordMoveUniCommand(sublime_plugin.TextCommand):
    """
    word_move_uni コマンドの実装。
    "by":"words" あるいは "by":"word_ends" 付きの move コマンドと同様だが、非ascii文字で適切なジャンプを行う。

    """

    #-----------------------------------------------------------------------------------------------------------
    def run(self, edit, forward=False, extend=False, by="words", **args):

        # by 引数に従ってストップする位置属性を決定。
        # これだとネイティブ挙動とは微妙に異なる(文字を囲うダブルクォートで止まるかどうかなど)のだが、まあ仕方なし。
        stopper = sublime.CLASS_LINE_START | sublime.CLASS_LINE_END | sublime.CLASS_EMPTY_LINE
        if by == "words":
            stopper |= sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START
        elif by == "word_ends":
            stopper |= sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END
        elif by == "subwords":
            stopper |= sublime.CLASS_SUB_WORD_START | sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START
        elif by == "subword_ends":
            stopper |= sublime.CLASS_SUB_WORD_END | sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END

        # 各選択領域を一つずつ処理して、新たな選択領域を取得。
        regions = [self.processOne(region, forward, stopper, extend) for region in self.view.sel()]

        # 新たな選択領域を反映する。
        self.view.sel().clear()
        self.view.sel().add_all(regions)

        # 領域が一つのみの場合に、移動後のキャレットが画面内に入るようにする。
        if len(regions) == 1:
            self.view.show(regions[0].b, False)

    #-----------------------------------------------------------------------------------------------------------
    def processOne(self, region, forward, stopper, extend):
        """
        指定された選択領域を新たにどうすればよいかを返す。
        """

        # キャレット位置からジャンプ先を求める。
        stop = findUniStop(self.view, region.b, forward, stopper)

        # 新たな選択領域をリターン。
        return sublime.Region(region.a if extend else stop, stop)


#===========================================================================================================
class WordSelectUniCommand(sublime_plugin.TextCommand):
    """
    word_select_uni コマンドの実装。
    drag_select コマンドと同様だが、非ascii文字も考慮したストップ位置を使う。
    """

    #-----------------------------------------------------------------------------------------------------------
    def want_event(self):
        """
        コマンド引数で "event" を受け取れるようにする。
        """
        return True

    #-----------------------------------------------------------------------------------------------------------
    def run(self, edit, by="words", **args):

        # ダブルクリックされた文字位置を取得して領域を修正する。
        firepoint = self.view.window_to_text((args["event"]["x"], args["event"]["y"]))

        # 追加でも解除でもないなら現在の選択状態はクリア。
        if not args.get("additive") and not args.get("subtractive"):
            self.view.sel().clear()

        # 引数で指定された文字位置における単語領域を取得する。
        region = makeWordRegion(self.view, firepoint, by)

        # "subtractive" オプションに従って反映する。
        if args.get("subtractive"):
            self.view.sel().subtract(region)
        else:
            self.view.sel().add(region)


#===========================================================================================================
class WordExpandUniCommand(sublime_plugin.TextCommand):
    """
    word_expand_uni コマンドの実装。
    空のRegionを持つ場合におけるfind_under_expandを、非ascii文字も考慮したストップ位置になるように代替する。
    """

    #-----------------------------------------------------------------------------------------------------------
    def run(self, edit, by="words"):

        # 各選択領域のうち、範囲が空のものを一つずつ処理する。
        for region in self.view.sel():
            if region.empty():
                self.processOne(region, by)

    #-----------------------------------------------------------------------------------------------------------
    def processOne(self, region, by):

        # 引数で指定された文字位置における単語領域を取得する。
        region = makeWordRegion(self.view, region.a, by)

        # 選択領域を拡張。
        self.view.sel().add(region)


#===========================================================================================================
PLUGIN_NAME = "JapanWordStop"

def plugin_loaded():
    """
    このプラグインがロードされたら呼ばれる。
    """

    # 設定ファイルの読み出しと、
    settings = sublime.load_settings(PLUGIN_NAME+".sublime-settings")
    loadSettings(settings)

    # 設定ファイルが変更されたときにリロードされるようにする。
    settings.add_on_change(PLUGIN_NAME, settingsChanged)

def plugin_unloaded():
    """
    このプラグインがアンロードされたときに参照が切れるようにする。
    """
    sublime.load_settings(PLUGIN_NAME+".sublime-settings").clear_on_change(PLUGIN_NAME)

def settingsChanged():
    """
    設定ファイルが変更されたら呼ばれる。
    """
    settings = sublime.load_settings(PLUGIN_NAME+".sublime-settings")
    loadSettings(settings)

def loadSettings(settings):
    """
    設定を読み出してグローバル変数に格納する。
    """
    global charGroups, intercept

    charGroups = settings.get("character_groups", {})
    intercept = settings.get("command_intercept", True)

    # character_groupsについては、すべて正規表現としてコンパイルしておく。
    # コンパイルエラーがある場合はステータスバーに表示。
    index = None
    try:
        for index, val in charGroups.items():
            charGroups[index] = re.compile(val)
    except sre_constants.error as err:
        charGroups = {}
        win = sublime.active_window()
        if win:
            win.status_message(PLUGIN_NAME+" character_groups compile error (" + index + "): " + str(err))
        raise err

#-----------------------------------------------------------------------------------------------------------
def makeWordRegion(view, firepoint, by):
    """
    指定された文字位置における単語を領域とする Region を作成する。
    """

    # 単語文字の直後にある空白文字が基点となる場合は、カーソルを一つ前に移して直前の単語が選択されるようにする。
    attrs = uniclassify(view, firepoint)
    if attrs & sublime.CLASS_WORD_END  and  not attrs & sublime.CLASS_WORD_START:
        firepoint -= 1

    # by 引数に従ってストップする位置属性を決定。
    normalStop = sublime.CLASS_LINE_START | sublime.CLASS_LINE_END | sublime.CLASS_EMPTY_LINE
    frontwardStop = normalStop | sublime.CLASS_WORD_END   | sublime.CLASS_PUNCTUATION_END
    backwardStop  = normalStop | sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START
    if by == "subwords":
        frontwardStop |= sublime.CLASS_SUB_WORD_END
        backwardStop  |= sublime.CLASS_SUB_WORD_START

    # 指定位置の単語の後方・前方境界をそれぞれ取得。
    # カーソル位置が単語境界である可能性があるので後方を取得する時はカーソルを一つ動しておく必要がある。
    a = findUniStop(view, firepoint+1, False, normalStop | backwardStop)
    b = findUniStop(view, firepoint, True, normalStop | frontwardStop)

    return sublime.Region(a, b)

#-----------------------------------------------------------------------------------------------------------
def findUniStop(view, pos, forward, stopper):
    """
    引数で指定された位置にある文字から、指定された方向へ単語境界を探す。
    """

    # 位置を一つずつ動かしながら属性を見ていく。
    while True:

        # カーソル移動。文書の端を超えたらリターン。
        pos += +1 if forward else -1
        if pos < 0:
            return 0
        if view.size() <= pos:
            return view.size()

        # 位置の属性を取得してストップする属性が含まれているならその位置でリターン。
        attrs = uniclassify(view, pos)
        if attrs & stopper:
            return pos

#-----------------------------------------------------------------------------------------------------------
def uniclassify(view, pos):
    """
    sublime標準のView.classify()と同じだが、非ascii文字も加味する。
    """

    # まずは標準のclassify()でascii文字列における属性を取得する。
    attr = view.classify(pos)

    # 指定された位置の左右の文字を取得。
    left = view.substr(pos-1)
    right = view.substr(pos)

    # どちらかが非asciiの場合のみ処理する。このifはあまり意味がない。ほとんどascii文字であろうから、高速化のために入れているだけ。
    if 0xFF < ord(left) or 0xFF < ord(right):

        # 両者の文字グループを取得。
        lgroup = getCharacterGroup(left)
        rgroup = getCharacterGroup(right)

        # 両者が同じグループなら追加の属性はない。グループが違う場合のみ、slip, punct, ascii, その他 の全組み合わせを処理する。
        if lgroup != rgroup:

            # 両者のグループが違うならこの属性は常に付く。
            attr |= sublime.CLASS_SUB_WORD_START
            attr |= sublime.CLASS_SUB_WORD_END

            # 右側が平仮名
            if rgroup == "slip":
                if lgroup == "slip":
                    pass
                elif lgroup == "punct":
                    attr |= sublime.CLASS_WORD_START
                    attr |= sublime.CLASS_PUNCTUATION_END
                elif lgroup == "ascii":
                    attr |= sublime.CLASS_WORD_START
                    if left != " " and not attr & (sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START):
                        attr |= sublime.CLASS_WORD_END
                else:
                    pass

            # 右側が記号
            elif rgroup == "punct":
                attr |= sublime.CLASS_PUNCTUATION_START
                if lgroup == "slip":
                    attr |= sublime.CLASS_WORD_END
                elif lgroup == "punct":
                    pass
                elif lgroup == "ascii":
                    if left != " " and not attr & (sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START):
                        attr |= sublime.CLASS_WORD_END
                else:
                    attr |= sublime.CLASS_WORD_END

            # 右側がascii
            elif rgroup == "ascii":
                if lgroup == "slip":
                    attr |= sublime.CLASS_WORD_END
                    if right != " " and not attr & (sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END):
                        attr |= sublime.CLASS_WORD_START
                elif lgroup == "punct":
                    attr |= sublime.CLASS_PUNCTUATION_END
                    if right != " " and not attr & (sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END):
                        attr |= sublime.CLASS_WORD_START
                elif lgroup == "ascii":
                    pass
                else:
                    attr |= sublime.CLASS_WORD_END
                    if right != " " and not attr & (sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END):
                        attr |= sublime.CLASS_WORD_START

            # 右側が漢字等
            else:
                attr |= sublime.CLASS_WORD_START
                if lgroup == "slip":
                    attr |= sublime.CLASS_WORD_END
                elif lgroup == "punct":
                    attr |= sublime.CLASS_PUNCTUATION_END
                elif lgroup == "ascii":
                    if left != " " and not attr & (sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START):
                        attr |= sublime.CLASS_WORD_END
                else:
                    attr |= sublime.CLASS_WORD_END

    return attr

#-----------------------------------------------------------------------------------------------------------
def getCharacterGroup(char):
    """
    引数で指定された文字のグループ名を返す。
    """
    global charGroups

    for name, rex in charGroups.items():
        if rex.match(char):
            return name

    return "others"

#-----------------------------------------------------------------------------------------------------------
def explainCharClass(flags):
    """
    引数でclassify()の戻り値を説明する文字列で返す。デバッグ用。
    """

    dic = {
        "WORD_START": sublime.CLASS_WORD_START,
        "WORD_END": sublime.CLASS_WORD_END,
        "PUNCTUATION_START": sublime.CLASS_PUNCTUATION_START,
        "PUNCTUATION_END": sublime.CLASS_PUNCTUATION_END,
        "SUB_WORD_START": sublime.CLASS_SUB_WORD_START,
        "SUB_WORD_END": sublime.CLASS_SUB_WORD_END,
        "LINE_START": sublime.CLASS_LINE_START,
        "LINE_END": sublime.CLASS_LINE_END,
        "EMPTY_LINE": sublime.CLASS_EMPTY_LINE,
        "WORD_MIDDLE?": 0b1000000000,
        "UNKNOWN_4FF?": 0b10000000000,
        "COMMA_RIGHT?": 0b100000000000,
        "COMMA_LEFT?":  0b10000000000000,
    }

    # フラグビットを一つずつチェック。ヒットしたフラグをリスト result に追加していく。
    result = []
    for k, v in dic.items():
        if flags & v:
            result.append(k)

    # 引数の値からチェックしたビットをOFFに。
    for k, v in dic.items():
        flags &= ~v

    # まだ値が残っている場合は、その二進表現を result に追加する。
    if flags:
        result.append(bin(flags))

    # カンマで連結してリターン。
    return ", ".join(result) if len(result) > 0 else "(none)"
