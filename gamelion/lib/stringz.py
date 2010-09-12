import struct, re

__all__ = ["pack", "unpack"]

initial = re.compile(r"^[@=<>!]")
format_element = re.compile(r"(\d*)([xcbB?hHiIlLqQfdspPz])")

def _scan_format_element(fmt):
    first = '@'
    settings = initial.match(fmt)
    if settings is not None:
        first = settings.group(0)

    return first, format_element.findall(fmt)

def pack(fmt, *args):
    first, format_args = _scan_format_element(fmt)
    format_string = first

    index = 0
    for repeat_count, format in format_args:
        if format == 'z':
            if repeat_count == '':
                count = 1
            else:
                count = int(repeat_count)

            for i in xrange(count):
                format_string += str(len(args[index]))
                format_string += 'sx'
                index += 1
        else:
            if repeat_count != '':
                format_string += repeat_count
            format_string += format
        index += 1

    return struct.pack(format_string, *args)

def unpack(fmt, string):
    first, format_args = _scan_format_element(fmt)
    results = []

    for repeat_count, format in format_args:
        if format == 'z':
            new_result, string = string.split('\x00', 1)
            results.append(new_result)
        else:
            local_format = first + repeat_count + format
            size = struct.calcsize(local_format)

            results.extend(struct.unpack(local_format, string[:size]))

            string = string[size:]

    return results
