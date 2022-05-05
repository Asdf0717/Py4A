import ctypes
import binascii

input_ = input("Upatre sample: ")


with open(input_, 'rb+') as file:
    data = file.read()[0x66d: 0x66d + 0xe40]
    uncompressed = ctypes.create_string_buffer(0x1200)
    final_size = ctypes.c_ulong(0)

    decoded = binascii.a2b_base64(data)

    list_ = []
    for i, n in enumerate(decoded):
        list_.append(decoded[i] ^ 0x4C)

    ctypes.windll.ntdll.RtlDecompressBuffer(2, uncompressed, 0x1200, ctypes.c_char_p(bytes(list_)), 0x1200,
                                            ctypes.byref(
                                                final_size))

    with open(input_ + ".extr.exe", "wb") as outfile:
        for n in list(uncompressed):
            outfile.write(n)