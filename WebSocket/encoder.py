import json
from bson.objectid import ObjectId

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj

def decoder(dct):
    for k, v in dct.items():
        if '_id' in dct:
            try:
                dct['_id'] = ObjectId(dct['_id'])
            except:
                pass
        return dct