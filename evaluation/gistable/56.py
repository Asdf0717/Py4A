import base64


##################### TEST: Get encoded image from some stream ####################

fo = open("a.txt", "rb")
content = fo.read()


##################### END #####################


def to_picture(img_encoded, full_path_file_name):
    content_decoded = base64.decodebytes(
        img_encoded)  # Just pass over the method the bytes array resulting of reading the file

    foo = open(full_path_file_name.encode('utf-8'), 'wb')
    foo.write(content_decoded)  # And write the decoded content to a file with a picture extension



    # TODO: Check extension in json file for correct saving.
    foo.close()


to_picture(content, "/home/bretanac93/baba.png")