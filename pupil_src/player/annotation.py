#coding: utf-8
import os
import json

class Annotation():
    def __init__(self, rec_dir):
        self.data = []
        self.filepath = os.path.join(rec_dir, "annotation.json")
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath) as f:
                self.data = dataFromJson(json.load(f))

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.json(), f)

    def beginAction(self, frameIndex):
        i = self.seek(frameIndex)

        self.data.insert(i, Element("begin", frameIndex))
        insertedIndex = i

        # 重複の除外
        i = insertedIndex + 1
        while i < len(self.data):
            e = self.data[i]
            if e.flg == "end": break
            if e.flg == "begin": self.data.pop(i)
            else: i += 1

        i = insertedIndex - 1
        while i >= 0:
            e = self.data[i]
            if e.flg == "end": break
            if e.flg == "begin": self.data.pop(i)
            i -= 1

        self.save()

    def endAction(self, frameIndex):
        i = self.seek(frameIndex)

        self.data.insert(i, Element("end", frameIndex))
        insertedIndex = i

        # 重複の除外
        i = insertedIndex + 1
        while i < len(self.data):
            e = self.data[i]
            if e.flg == "begin": break
            if e.flg == "end": self.data.pop(i)
            else: i += 1

        i = insertedIndex - 1
        while i >= 0:
            e = self.data[i]
            if e.flg == "begin": break
            if e.flg == "end": self.data.pop(i)
            i -= 1

        self.save()

    def removeAction(self, frameIndex):
        i = self.seek(frameIndex)

        if self.data[i].flg == "begin":
            self.data.pop(i)
            self.data.pop(i+1)

        self.save()

    def seek(self, frameIndex):
        i = 0
        for e in self.data:
            if frameIndex < e.frameIndex: break
            i += 1
        return i

    def isAction(self, frameIndex):
        i = self.seek(frameIndex)
        if i == 0: return False
        return self.data[i-1].flg == "begin"

    def json(self):
        return jsonFromData(self.data)


def jsonFromData(data):
    return [[e.flg, e.frameIndex] for e in data]

def dataFromJson(json):
    return [Element(e[0], e[1]) for e in json]


class Element():
    def __init__(self, flg, frameIndex):
        self.flg = flg
        self.frameIndex = frameIndex


if __name__ == "__main__":
    a = Annotation("/tmp")
    a.beginAction(3)
    a.endAction(5)
    a.beginAction(2)
    a.endAction(6)
    a.beginAction(7)
    a.endAction(8)
    print jsonFromData(a.data)
    for i in range(10):
        print i, a.isAction(i)

