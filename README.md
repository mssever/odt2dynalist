# ODT to Dynalist Converter

## Introduction
This project is a set of scripts I developed to convert a bunch of LibreOffice ODT files containing speaking notes to a format suitable for pasting into [Dynalist](https://dynalist.io). I'm releasing them in case they can help someone else. However, _some assembly is required_. There are many ways to format lists in LibreOffice/OpenOffice, and I made no attempt to account for any of them except for the one I use.

Because of the Some Assembly Required nature of these scripts, you should have at least basic familiarity with both Python and Bash.

You're welcome to fork it and modify it to suit your needs. If you modify it in a way that doesn't break existing functionality, feel free to send me a pull request. If it works without modification, count yourself lucky.

## Prerequisites
I developed this on a Linux machine using LibreOffice 5.1.4.2. It will probably work on other operating systems and with OpenOffice, but I haven't tested any other setup.

### Minimum requirements
If you meet these requirements, you'll be able to run the conversion script, but you'll have to interact with LibreOffice manually.

- Python 3
- Beautiful Soup 4 (only required for HTML mode). In Ubuntu, the package is `python-bs4`. For other systems, Google is your friend.

### Optimal requirements
To take full advantage of the scripts, make sure you meet these requirements in addition to the minimum requirements above:

- Bash on any supported OS: Linux, Mac OS, Windows 10, etc.
- W3C's [Tidy](http://www.html-tidy.org/). The Ubuntu package is called `tidy`.
- LibreOffice (I presume OpenOffice will also work, but I haven't tested it.)
- A way to copy from the command line to the clipboard:
    - If you have X11 (as most Linux users have), you need `xsel`. The Ubuntu package is also called `xsel`.
    - If you have another environment (Windows 10, Mac OS, Mir, etc.), you'll need to research which tool to use and modify the `odt2html` and/or `odt2txt` scripts accordingly.

## Configuration
Read through the file `sermons_to_python.py` and make any changes necessary to ensure compatibility with your source files. I can't give you specific instructions here, except to note that text mode is most likely the easiest to make work if your source files are compatible. See the comments in the script file for details. Text mode, however, can't convert any formatting or footnotes.

If you want to preserve formatting, you have to use HTML mode. I hope that HTML mode will work without configuration, but I make no promises. In particular, it only preserves bold, italic, and footnotes. If you want to preserve any other formatting, you'll need to modify the script. Pull requests that preserve additional formatting are welcome.

## Usage
Once everything is configured properly, run either `odt2txt` or `odt2html`. `odt2html` preserves some formatting, so it's preferred. However, depending on how your sources files are structured, you may need to fall back to `odt2txt`.

    ./odt2html /path/to/input/document.odt

The script will convert the file and copy the result to your clipboard. You should then be able to paste directly into Dynalist.

If the document contained footnotes, they'll have the `#fixme` hashtag added to them, because pasting directly into a Dynalist note isn't supported. You can do a search on Dynalist for `#fixme` and manually cut and paste the footnotes into Dynalist notes.

## Known Issues
Some things don't work as well as I'd like them to. Here are the known issues:

- LibreOffice is a real nuisance to work with via script. The conversion will fail silently if it is running when you invoke `odt2html` or `odt2txt`. The scripts try to check for this and print an error message if LibreOffice and/or OpenOffice is running, but the check isn't foolproof. If you're getting errors, make sure that LibreOffice/OpenOffice is complely shut down, including any background processes.
- For some reason, [I can't paste directly into Dynalist on Chromium](http://askubuntu.com/q/850991/13398). Instead, I have to paste into a text editor, select all, cut, then past into Dynalist. If you know of a solution, I'd love to hear about it.
- If you can't use `xsel` or an equivalent program (see the optimal requirements section above), you'll need to modify `odt2html` and/or `odt2txt` to make them leave an output file around that you can open and manually copy from:
    - For `odt2html`, you need to keep the file `html/$BASE.html.txt` around until you've copied the data from it.
    - For `odt2txt`, you need the file `txt/$BASE.txt`.
