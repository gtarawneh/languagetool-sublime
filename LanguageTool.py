"""
LanguageTool.py

This is a simple Sublime Text plugin for checking grammar. It passes buffer
content to LanguageTool (via http) and highlights reported problems.
"""

import sublime
import sublime_plugin
import subprocess
import os.path
import fnmatch


def _is_ST2():
    return (int(sublime.version()) < 3000)


if _is_ST2():
    import LTServer
    import LanguageList
else:
    from . import LTServer
    from . import LanguageList


def move_caret(view, i, j):
    """Select character range [i, j] in view."""
    target = view.text_point(0, i)
    view.sel().clear()
    view.sel().add(sublime.Region(target, target + j - i))


def set_status_bar(str):
    """Change status bar message."""
    sublime.status_message(str)


def select_problem(view, prob):
    reg = view.get_regions(prob['regionKey'])[0]
    move_caret(view, reg.a, reg.b)
    view.show_at_center(reg)
    show_problem(prob)


def is_problem_solved(v, p):
    rl = v.get_regions(p['regionKey'])
    if len(rl) == 0:
        print('tried to find non-existing region with key ' + p['regionKey'])
        return True
    r = rl[0]
    # a problem is solved when either:
    # 1. its region has zero length
    # 2. its contents have been changed
    return r.empty() or (v.substr(r) != p['orgContent'])


def show_problem(p):
    """Show problem description and suggestions."""

    def show_problem_panel(p):
        msg = p['message']
        if p['replacements']:
            msg += '\n\nSuggestion(s): ' + ', '.join(p['replacements'])
        if p['urls']:
            msg += '\n\nMore Info: ' + '\n'.join(p['urls'])
        show_panel_text(msg)

    def show_problem_status_bar(p):
        if p['replacements']:
            msg = u"{0} ({1})".format(p['message'], p['replacements'])
        else:
            msg = p['message']
        sublime.status_message(msg)

    # call appropriate show_problem function

    use_panel = get_settings().get('display_mode') == 'panel'
    show_fun = show_problem_panel if use_panel else show_problem_status_bar
    show_fun(p)


def show_panel_text(str):
    if _is_ST2():
        window = sublime.active_window()
        pt = window.get_output_panel("languagetool")
        pt.set_read_only(False)
        edit = pt.begin_edit()
        pt.insert(edit, pt.size(), str)
        window.run_command("show_panel", {"panel": "output.languagetool"})
    else:
        sublime.active_window().run_command('set_language_tool_panel_text', {
            'str': str
        })


class setLanguageToolPanelTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, str):
        window = sublime.active_window()
        pt = window.get_output_panel("languagetool")
        pt.settings().set("wrap_width", 0)
        pt.settings().set("word_wrap", True)
        pt.set_read_only(False)
        pt.insert(edit, pt.size(), str)
        window.run_command("show_panel", {"panel": "output.languagetool"})


# navigation function
class gotoNextLanguageProblemCommand(sublime_plugin.TextCommand):
    def run(self, edit, jump_forward=True):
        v = self.view
        problems = v.__dict__.get("problems", [])
        if len(problems) > 0:
            sel = v.sel()[0]
            if jump_forward:
                for p in problems:
                    r = v.get_regions(p['regionKey'])[0]
                    if (not is_problem_solved(v, p)) and (sel.begin() < r.a):
                        select_problem(v, p)
                        return
            else:
                for p in reversed(problems):
                    r = v.get_regions(p['regionKey'])[0]
                    if (not is_problem_solved(v, p)) and (r.a < sel.begin()):
                        select_problem(v, p)
                        return
        set_status_bar("no further language problems to fix")
        sublime.active_window().run_command("hide_panel", {
            "panel": "output.languagetool"
        })


class clearLanguageProblemsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        problems = v.__dict__.get("problems", [])
        for p in problems:
            v.erase_regions(p['regionKey'])
        problems = []
        recompute_highlights(v)
        caretPos = self.view.sel()[0].end()
        v.sel().clear()
        sublime.active_window().run_command("hide_panel", {
            "panel": "output.languagetool"
        })
        move_caret(v, caretPos, caretPos)


class markLanguageProblemSolvedCommand(sublime_plugin.TextCommand):
    def run(self, edit, apply_fix):
        v = self.view
        problems = v.__dict__.get("problems", [])
        sel = v.sel()[0]
        for p in problems:
            r = v.get_regions(p['regionKey'])[0]
            replacements = p['replacements']
            nextCaretPos = r.a
            if r == sel:
                if apply_fix and replacements:
                    # fix selected problem:
                    if len(replacements) > 1:

                        def callbackF(i):
                            self.choose_suggestion(v, p, replacements, i)

                        v.window().show_quick_panel(replacements, callbackF)
                        return
                    else:
                        v.replace(edit, r, replacements[0])
                        nextCaretPos = r.a + len(replacements[0])
                else:
                    # ignore problem:
                    if p['category'] == "Possible Typo":
                        # if this is a typo then include all identical typos in
                        # the list of problems to be fixed
                        pID = lambda py: (py['category'], py['orgContent'])
                        ignoreProbs = [
                            px for px in problems if pID(p) == pID(px)
                        ]
                    else:
                        # otherwise select just this one problem
                        ignoreProbs = [p]
                    for p2 in ignoreProbs:
                        ignore_problem(p2, v, self, edit)
                # after either fixing or ignoring:
                move_caret(v, nextCaretPos,
                           nextCaretPos)  # move caret to end of region
                v.run_command("goto_next_language_problem")
                return
        # if no problems are selected:
        set_status_bar('no language problem selected')

    def choose_suggestion(self, v, p, replacements, choice):
        """Handle suggestion list selection."""
        problems = v.__dict__.get("problems", [])
        if choice != -1:
            r = v.get_regions(p['regionKey'])[0]
            v.run_command('insert', {'characters': replacements[choice]})
            c = r.a + len(replacements[choice])
            move_caret(v, c, c)  # move caret to end of region
            v.run_command("goto_next_language_problem")
        else:
            select_problem(v, p)


def get_settings():
    return sublime.load_settings('LanguageTool.sublime-settings')


class startLanguageToolServerCommand(sublime_plugin.TextCommand):
    """Launch local LanguageTool Server."""

    def run(self, edit):

        jar_path = get_settings().get('languagetool_jar')

        if not jar_path:
            show_panel_text("Setting languagetool_jar is undefined")
            return

        if not os.path.isfile(jar_path):
            show_panel_text(
                'Error, could not find LanguageTool\'s JAR file (%s)'
                '\n\n'
                'Please install LT in this directory'
                ' or modify the `languagetool_jar` setting.' % jar_path)
            return

        sublime.status_message('Starting local LanguageTool server ...')

        cmd = ['java', '-jar', jar_path, '-t']

        if sublime.platform() == "windows":
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.SW_HIDE)
        else:
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)


class changeLanguageToolLanguageCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.languages = LanguageList.languages
        languageNames = [x[0] for x in self.view.languages]
        handler = lambda ind: handle_language_selection(ind, self.view)
        self.view.window().show_quick_panel(languageNames, handler)


def handle_language_selection(ind, view):
    key = 'language_tool_language'
    if ind == 0:
        view.settings().erase(key)
    else:
        selected_language = view.languages[ind][1]
        view.settings().set(key, selected_language)


def get_language(view):
    key = 'language_tool_language'
    return view.settings().get(key, 'auto')


def ignore_problem(p, v, self, edit):
    # change region associated with this problem to a 0-length region
    r = v.get_regions(p['regionKey'])[0]
    dummyRg = sublime.Region(r.a, r.a)
    hscope = get_settings().get("highlight-scope", "comment")
    v.add_regions(p['regionKey'], [dummyRg], hscope, "", sublime.DRAW_OUTLINED)
    # dummy edit to enable undoing ignore
    v.insert(edit, v.size(), "")


def load_ignored_rules():
    ignored_rules_file = 'LanguageToolUser.sublime-settings'
    settings = sublime.load_settings(ignored_rules_file)
    return settings.get('ignored', [])


def save_ignored_rules(ignored):
    ignored_rules_file = 'LanguageToolUser.sublime-settings'
    settings = sublime.load_settings(ignored_rules_file)
    settings.set('ignored', ignored)
    sublime.save_settings(ignored_rules_file)


def get_server(settings, force_server):
    """Return LT server url based on settings.

    The returned url is for either the local or remote servers, defined by the
    settings entries:

        - language_server_local
        - language_server_remote

    The choice between the above is made based on the settings value
    'default_server'. If not None, `force_server` will override this setting.

    """
    server_setting = force_server or settings.get('default_server')
    setting_name = 'languagetool_server_%s' % server_setting
    server = settings.get(setting_name)
    return server


class LanguageToolCommand(sublime_plugin.TextCommand):
    def run(self, edit, force_server=None):
        v = self.view
        problems = list()
        v.problems = problems
        settings = get_settings()
        server = get_server(settings, force_server)
        hscope = settings.get("highlight-scope", "comment")
        ignored = load_ignored_rules()
        strText = v.substr(sublime.Region(0, v.size()))
        checkRegion = v.sel()[0]
        if checkRegion.empty():
            checkRegion = sublime.Region(0, v.size())
        v.run_command("clear_language_problems")
        lang = get_language(v)
        ignoredIDs = [rule['id'] for rule in ignored]
        matches = LTServer.getResponse(server, strText, lang, ignoredIDs)
        if matches == None:
            set_status_bar(
                'could not parse server response'
                ' (may be due to quota if using http://languagetool.org)')
            return
        for match in matches:
            problem = {
                'category': match['rule']['category']['name'],
                'message': match['message'],
                'replacements': [r['value'] for r in match['replacements']],
                'rule': match['rule']['id'],
                'urls': [w['value'] for w in match['rule'].get('urls', [])],
            }
            offset = match['offset']
            length = match['length']
            region = sublime.Region(offset, offset + length)
            if not checkRegion.contains(region):
                continue
            ignored_scopes = settings.get('ignored-scopes', [])
            # view.scope_name() returns a string of space-separated scope names
            # (ending with a space)
            pscopes = v.scope_name(region.a).split(' ')[0:-1]
            for ps in pscopes:
                if any([fnmatch.fnmatch(ps, i) for i in ignored_scopes]):
                    ignored = True
                    break
            else:
                # none of this region's scopes are ignored
                regionKey = str(len(problems))
                v.add_regions(regionKey, [region], hscope, "",
                              sublime.DRAW_OUTLINED)
                problem['orgContent'] = v.substr(region)
                problem['regionKey'] = regionKey
                problems.append(problem)
        if problems:
            select_problem(v, problems[0])
        else:
            set_status_bar("no language problems were found :-)")


class DeactivateRuleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        ignored = load_ignored_rules()
        v = self.view
        problems = v.__dict__.get("problems", [])
        sel = v.sel()[0]
        selected = [
            p for p in problems
            if sel.contains(v.get_regions(p['regionKey'])[0])
        ]
        if not selected:
            set_status_bar('select a problem to deactivate its rule')
        elif len(selected) == 1:
            rule = {
                "id": selected[0]['rule'],
                "description": selected[0]['message']
            }
            ignored.append(rule)
            ignoredProblems = [p for p in problems if p['rule'] == rule['id']]
            for p in ignoredProblems:
                ignore_problem(p, v, self, edit)
            problems = [p for p in problems if p['rule'] != rule['id']]
            v.run_command("goto_next_language_problem")
            save_ignored_rules(ignored)
            set_status_bar('deactivated rule %s' % rule)
        else:
            set_status_bar('there are multiple selected problems;'
                           ' select only one to deactivate')


class ActivateRuleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        ignored = load_ignored_rules()
        if ignored:
            activate_callback_wrapper = lambda i: self.activate_callback(i)
            ruleList = [[rule['id'], rule['description']] for rule in ignored]
            self.view.window().show_quick_panel(ruleList,
                                                activate_callback_wrapper)
        else:
            set_status_bar('there are no ignored rules')

    def activate_callback(self, i):
        ignored = load_ignored_rules()
        if i != -1:
            activate_rule = ignored[i]
            ignored.remove(activate_rule)
            save_ignored_rules(ignored)
            set_status_bar('activated rule %s' % activate_rule['id'])


class LanguageToolListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        # buffer text was changed, recompute region highlights
        recompute_highlights(view)


def recompute_highlights(view):
    problems = view.__dict__.get("problems", {})
    hscope = get_settings().get("highlight-scope", "comment")
    for p in problems:
        rL = view.get_regions(p['regionKey'])
        if rL:
            regionScope = "" if is_problem_solved(view, p) else hscope
            view.add_regions(p['regionKey'], rL, regionScope, "",
                             sublime.DRAW_OUTLINED)
