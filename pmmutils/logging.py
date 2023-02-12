import logging, os, platform, psutil, sys
import traceback
from logging.handlers import RotatingFileHandler

logger = None

def my_except_hook(exctype, value, tb):
    if issubclass(exctype, KeyboardInterrupt):
        sys.__excepthook__(exctype, value, tb)
    elif logger:
        logger.critical(f"Traceback (most recent call last):\n{traceback.format_tb(tb)[0]}{exctype.__name__}: {value}")

class RedactingFormatter(logging.Formatter):
    _secrets = []

    def __init__(self, orig_format, secrets=None):
        self.orig_formatter = logging.Formatter(orig_format)
        if secrets:
            self._secrets.extend(secrets)
        super().__init__()

    def format(self, record):
        msg = self.orig_formatter.format(record)
        for secret in self._secrets:
            if secret:
                msg = msg.replace(secret, "(redacted)")
        return msg

    def __getattr__(self, attr):
        return getattr(self.orig_formatter, attr)

def fmt_filter(record):
    record.levelname = f"[{record.levelname}]"
    record.filename = f"[{record.filename}:{record.lineno}]"
    return True

class PMMLogger:
    def __init__(self, name, log_dir, log_file=None, screen_width=100, separating_character="=", filename_spacing=27, ignore_ghost=False, is_debug=True, is_trace=False, log_requests=False):
        global logger
        logger = self
        sys.excepthook = my_except_hook
        self.name = name
        self.log_dir = log_dir
        self.log_file = log_file
        self.screen_width = screen_width
        self.separating_character = separating_character
        self.filename_spacing = filename_spacing
        self.is_debug = is_debug
        self.is_trace = is_trace
        self.log_requests = log_requests
        self.ignore_ghost = ignore_ghost
        self.warnings = {}
        self.errors = {}
        self.criticals = {}
        self.spacing = 0
        if not self.log_file:
            self.log_file = f"{self.name}.log"
        os.makedirs(self.log_dir, exist_ok=True)
        self._logger = logging.getLogger(None if self.log_requests else self.name)
        self._logger.setLevel(logging.DEBUG)
        cmd_handler = logging.StreamHandler()
        cmd_handler.setLevel(logging.DEBUG if self.is_debug else logging.INFO)
        self._formatter(handler=cmd_handler)
        self._logger.addHandler(cmd_handler)
        main_handler = self._add_handler(self.log_file, count=9)
        main_handler.addFilter(fmt_filter)
        self._logger.addHandler(main_handler)
        self.old__log = self._logger._log
        self._logger._log = self.new__log

    def new__log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, center=False, stacklevel=2):
        trace = level == logging.NOTSET
        log_only = False
        msg = str(msg)
        if center:
            msg = self._centered(msg)
        if trace:
            level = logging.DEBUG
        if trace or msg.startswith("|"):
            self._formatter(trace=trace, border=not msg.startswith("|"))
        if self.spacing > 0:
            self.exorcise()
        if "\n" in msg:
            for i, line in enumerate(msg.split("\n")):
                self.old__log(level, line, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)
                if i == 0:
                    self._formatter(log_only=True, space=True)
            log_only = True
        else:
            self.old__log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)

        if trace or log_only or msg.startswith("|"):
            self._formatter()

    def _add_handler(self, log_file, count=3):
        _handler = RotatingFileHandler(log_file, delay=True, mode="w", backupCount=count, encoding="utf-8")
        self._formatter(handler=_handler)
        if os.path.isfile(log_file):
            self._logger.removeHandler(_handler)
            _handler.doRollover()
            self._logger.addHandler(_handler)
        return _handler

    def _formatter(self, handler=None, border=True, trace=False, log_only=False, space=False):
        console = f"%(message)-{self.screen_width - 2}s"
        console = f"| {console} |" if border else console
        file = f"{' ' * 65}" if space else f"[%(asctime)s] %(filename)-{self.filename_spacing}s {'[TRACE]   ' if trace else '%(levelname)-10s'} "
        handlers = [handler] if handler else self._logger.handlers
        for h in handlers:
            if not log_only or isinstance(h, RotatingFileHandler):
                h.setFormatter(RedactingFormatter(f"{file if isinstance(h, RotatingFileHandler) else ''}{console}"))

    def _centered(self, text, sep=" ", side_space=True, left=False):
        text = str(text)
        if len(text) > self.screen_width - 2:
            return text
        space = self.screen_width - len(text) - 2
        text = f"{' ' if side_space else sep}{text}{' ' if side_space else sep}"
        if space % 2 == 1:
            text += sep
            space -= 1
        side = int(space / 2) - 1
        final_text = f"{text}{sep * side}{sep * side}" if left else f"{sep * side}{text}{sep * side}"
        return final_text

    def separator(self, text=None, space=True, border=True, debug=False, trace=False, side_space=True, left=False):
        if trace and not self.is_trace:
            return None
        sep = " " if space else self.separating_character
        border_text = f"|{self.separating_character * self.screen_width}|"
        if border:
            self.print(border_text, debug=debug, trace=trace)
        if text:
            text_list = text.split("\n")
            for t in text_list:
                msg = f"|{sep}{self._centered(t, sep=sep, side_space=side_space, left=left)}{sep}|"
                self.print(msg, debug=debug, trace=trace)
            if border:
                self.print(border_text, debug=debug, trace=trace)

    def print(self, msg, critical=False, error=False, warning=False, debug=False, trace=False):
        if critical:
            self.critical(msg, stacklevel=4)
        elif error:
            self.error(msg, stacklevel=4)
        elif warning:
            self.warning(msg, stacklevel=4)
        elif debug:
            self.debug(msg, stacklevel=4)
        elif trace:
            self.trace(msg, stacklevel=4)
        else:
            self.info(msg, stacklevel=4)

    def trace(self, msg="", center=False, stacklevel=2):
        if self.is_trace:
            self.new__log(logging.NOTSET, msg, [], center=center, stacklevel=stacklevel)

    def debug(self, msg="", center=False, stacklevel=2):
        if self._logger.isEnabledFor(logging.DEBUG):
            self.new__log(logging.DEBUG, msg, [], center=center, stacklevel=stacklevel)

    def info(self, msg="", center=False, stacklevel=2):
        if self._logger.isEnabledFor(logging.INFO):
            self.new__log(logging.INFO, msg, [], center=center, stacklevel=stacklevel)

    def warning(self, msg="", center=False, group=None, ignore=False, stacklevel=2):
        if self._logger.isEnabledFor(logging.WARNING):
            if not ignore:
                if group not in self.warnings:
                    self.warnings[group] = []
                self.warnings[group].append(msg)
            self.new__log(logging.WARNING, msg, [], center=center, stacklevel=stacklevel)

    def error(self, msg="", center=False, group=None, ignore=False, stacklevel=2):
        if self._logger.isEnabledFor(logging.ERROR):
            if not ignore:
                if group not in self.errors:
                    self.errors[group] = []
                self.errors[group].append(msg)
            self.new__log(logging.ERROR, msg, [], center=center, stacklevel=stacklevel)

    def critical(self, msg="", center=False, group=None, ignore=False, exc_info=None, stacklevel=2):
        if self._logger.isEnabledFor(logging.CRITICAL):
            if not ignore:
                if group not in self.criticals:
                    self.criticals[group] = []
                self.criticals[group].append(msg)
            self.new__log(logging.CRITICAL, msg, [], center=center, exc_info=exc_info, stacklevel=stacklevel)

    def stacktrace(self, trace=False):
        self.print(traceback.format_exc(), debug=not trace, trace=trace)

    def _space(self, display_title):
        display_title = str(display_title)
        space_length = self.spacing - len(display_title)
        if space_length > 0:
            display_title += " " * space_length
        return display_title

    def ghost(self, text):
        if not self.ignore_ghost:
            try:
                final_text = f"| {text}"
            except UnicodeEncodeError:
                text = text.encode("utf-8")
                final_text = f"| {text}"
            print(self._space(final_text), end="\r")
            self.spacing = len(text) + 2

    def exorcise(self):
        if not self.ignore_ghost:
            print(self._space(" "), end="\r")
            self.spacing = 0

    def secret(self, text):
        if text and str(text) not in RedactingFormatter.secrets:
            RedactingFormatter.secrets.append(str(text))

    def header(self, pmm_args, name=None):
        self.separator()
        self.info(self._centered(" ____  _             __  __      _          __  __                                   "))
        self.info(self._centered("|  _ \\| | _____  __ |  \\/  | ___| |_ __ _  |  \\/  | __ _ _ __   __ _  __ _  ___ _ __ "))
        self.info(self._centered("| |_) | |/ _ \\ \\/ / | |\\/| |/ _ \\ __/ _` | | |\\/| |/ _` | '_ \\ / _` |/ _` |/ _ \\ '__|"))
        self.info(self._centered("|  __/| |  __/>  <  | |  | |  __/ || (_| | | |  | | (_| | | | | (_| | (_| |  __/ |   "))
        self.info(self._centered("|_|   |_|\\___/_/\\_\\ |_|  |_|\\___|\\__\\__,_| |_|  |_|\\__,_|_| |_|\\__,_|\\__, |\\___|_|   "))
        self.info(self._centered("                                                                     |___/           "))
        if name:
            self.info(self._centered(name))

        self.info(f"    Version: {pmm_args.local_version} {pmm_args.system_version}")
        if pmm_args.update_version:
            self.info(f"    Newest Version: {pmm_args.update_version}")
        self.info(f"    Platform: {platform.platform()}")
        self.info(f"    Memory: {round(psutil.virtual_memory().total / (1024.0 ** 3))} GB")
        self.separator()

        run_arg = " ".join([f'"{s}"' if " " in s else s for s in sys.argv[:]])
        self.debug(f"Run Command: {run_arg}")
        for o in pmm_args.options:
            self.debug(f"--{o['key']} ({o['env']}): {pmm_args.choices[o['key']]}")

    def error_report(self, title_only=False):
        self.separator()
        self.info(self._centered("Error Report"))
        self.separator()
        if not title_only and None in self.errors:
            self.info()
            self.info("Generic Errors: ")
            for e in self.errors[None]:
                self.error(f"  {e}", ignore=True)
        for title, errs in self.errors.items():
            if title is None:
                continue
            self.info()
            self.info(f"{title} Errors: ")
            for e in errs:
                self.error(f"  {e}", ignore=True)


