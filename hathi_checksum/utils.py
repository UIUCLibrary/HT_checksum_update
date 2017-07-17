import cmd
import hashlib
import typing

class CallAbort(Exception):
    pass


class ValidationError(Exception):
    pass


class InvalidChecksum(ValidationError):
    pass


class YesNo(cmd.Cmd):

    answer = None  # type: ignore

    def __init__(self, question):
        YesNo.prompt = "{} (yes/no/quit): ".format(question)
        # if intro:
        #     YesNo.intro = intro
        super().__init__()

    def do_yes(self, args)->bool:
        self._yes()
        return True

    def do_y(self, args):
        self._yes()
        return True

    def do_no(self, args):
        self._no()
        return True

    def do_n(self, args):
        self._no()
        return True

    def do_quit(self, args):
        self._abort()

    def do_q(self, args):
        self._abort()

    def default(self, line):
        print("Invalid answer, {}".format(line))

    # REAL answers
    @staticmethod
    def _abort():
        raise CallAbort()

    def _no(self):
        self.answer = False

    def _yes(self):
        self.answer = True


def ask(question, intro=None):
    query = YesNo(question)
    query.cmdloop(intro)
    answer = query.answer
    return answer


def calculate_md5(filename, chunk_size=8192):
    md5 = hashlib.md5()

    with open(filename, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()
