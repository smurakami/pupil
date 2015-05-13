#coding: utf-8
import os
import json

class Annotation():
    def __init__(self, rec_dir):
        self.data = []
        self.filepath = os.path.join(rec_dir, "annotation.json")
        try:
            with open(self.filepath) as f:
                self.data = json.load(f)
        except:
            pass

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

    def jsonFromData(self, data):
        return [[e.flg, e.frameIndex] for e in data]

    def dataFromJson(self, json):
        return [Element(e[0], e[1]) for e in json]

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.jsonFromData(self.data), f)


class Element():
    def __init__(self, flg, frameIndex):
        self.flg = flg
        self.frameIndex = frameIndex


if __name__ == "__main__":
    a = Annotation("/tmp")
    print a.jsonFromData(a.data)
    a.beginAction(3)
    print a.jsonFromData(a.data)
    a.endAction(5)
    print a.jsonFromData(a.data)
    a.beginAction(2)
    print a.jsonFromData(a.data)
    a.endAction(6)
    print a.jsonFromData(a.data)
    a.beginAction(7)
    print a.jsonFromData(a.data)
    a.endAction(8)
    print a.jsonFromData(a.data)

