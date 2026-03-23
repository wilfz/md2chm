#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib
from typing import Optional
import argparse
from sys import argv
import os
import re
import subprocess
import shlex
import shutil

#CONVERT_CMD = 'pandoc --from=gfm --to=html5 "{file}.md" --embed-resources --standalone --css="..\\Documentation\\github.css" --output="{file}.html"'
CONVERT_CMD = 'pandoc --from=gfm --to=html5 "{file}.md" --standalone --output="{file}.html"'
#CONVERT_CMD = 'pandoc --from=gfm --to=html5 "{file}.md" {css_path} --output="{file}.html"'

HELP_PROJECT_HEADER = """[OPTIONS]
Compatibility=1.1 or later
Compiled file={target}.chm
Contents file={target}.hhc
Default topic={default_topic}
Display compile progress=No
Error log file={target}.log1
Language=0x409 Englisch (Vereinigte Staaten)
Title={title}

[FILES]
"""

HELP_PROJECT_FOOTER = """
[INFOTYPES]
"""

TOC_HEADER = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD><BODY>
<OBJECT type="text/site properties">
	<param name="Window Styles" value="0x800025">
</OBJECT>
"""

TOC_FOOTER = "</BODY></HTML>\n"

_HEADER_RE = re.compile(r'^(#{1,4})\s+(.*)')  # match "# ", "## ", "### " followed by header text
_INVALID_FN_CHARS = re.compile(r'[\\/*?:"<>| ]')


def _sanitize_filename(name: str, max_len: int = 100) -> str:
    name = (name or "").strip()
    name = _INVALID_FN_CHARS.sub('_', name)
    name = re.sub(r'\s+', ' ', name)
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "section"


def convert_to_html(
    md_path: str, 
    command_template: str = None, 
    css_path: str = "",
    use_shell: bool = False, 
    command_cwd: str = None
) -> None:
    """
    Execute command line program pandoc for `md_path`. 
    `command_template` may contain placeholders `{file}` or `{path}` which will be 
    replaced with the file path.
    css_path is an optional path to a CSS file to be used in the generated HTML file.
    If `use_shell` is True the command is executed through the shell.
    """
    if not command_template:
        return

    cmd = command_template.format(file=md_path, path=md_path, css_path = css_path)

    try:
        if use_shell:
            # run via shell (command is a single string)
            proc = subprocess.run(cmd, shell=True, cwd=command_cwd, capture_output=True, text=True)
        else:
            # split into argv list for safe execution
            argv = shlex.split(cmd)
            proc = subprocess.run(argv, shell=False, cwd=command_cwd, capture_output=True, text=True)

        if proc.returncode != 0:
            print(f"Command failed for {md_path}: returncode={proc.returncode}")
            if proc.stdout:
                print("stdout:", proc.stdout.strip())
            if proc.stderr:
                print("stderr:", proc.stderr.strip())
    except Exception as e:
        print(f"Failed to run command for {md_path}: {e}")

    # end of convert_to_html()


def adjust_html(html_filename: str, href_dict: dict) -> None:
    """
    Read `html_filename`, apply small post-processing transformations and write
    the result back to the same path.

    Transformations:
      - Add target="_blank" to external https links
      - Restore code element font sizes
      - Replace internal href anchors with generated html filenames based on href_dict
    """

    html_fh = open(html_filename, "r", encoding="utf-8", errors="replace")
    if html_fh:
        # read entire file content into strin variable s
        s = html_fh.read()
        html_fh.close

        # add target="_blank" to external hyperlinks
        s = s.replace('<a href="https://', '<a target="_blank" href="https://')
        s = s.replace('<a\nhref="https://', '<a target="_blank"\nhref="https://')
        # don't reduce the font size of code elements:
        s = s.replace('font-size: 85%;', 'font-size: 100%;')
        # don't show vetrtical scroll bar
        s = s.replace('<pre><code>', '<pre style="overflow-y: hidden;"><code>')
        # add 2 empty lines (literally) to prevent horizontal scroll bar from overlaying the text
        s = s.replace('</code></pre>', '\n\n</code></pre>')

        # replace internal hyperlinks with filenames 
        # of generated html files according to href_dict
        for link in href_dict:
            search = f'<a href="{link}"'
            replmnt = f'<a href="{href_dict[link]}"'
            s = s.replace(search, replmnt)
            search = f'<a\nhref="{link}"'
            replmnt = f'<a\nref="{href_dict[link]}"'
            s = s.replace(search, replmnt)

        try:
            html_fh = open(html_filename, "w", encoding="utf-8")
            html_fh.write(s)
        except Exception as e:
            print(f"Failed to write processed html to {html_filename}: {e}")
        finally:
            if html_fh:
                html_fh.close()
    # end of adjust_html()


def compile_chm(target_name: str) -> None:
    """
    Try to compile the generated help project (`{target_name}.hhp`).
    Prefers FreePascal's `chmcmd.exe` if available, otherwise uses Microsoft
    HTML Help Workshop `hhc.exe` (Program Files(x86) path).
    Prints compiler output and errors if the invoked command returns output.
    """
    cmd = None
    if shutil.which("chmcmd.exe"):
        # use chmcmd from FreePascal to compile the help project file
        cmd = f'chmcmd --no-html-scan "{target_name}.hhp"'
    else:
        # use Microsoft HTML Help Workshop to compile the help project file
        prog_x86 = os.getenv("ProgramFiles(x86)")
        hhc = f"{prog_x86}\\HTML Help Workshop\\hhc.exe" if prog_x86 else None
        if hhc and os.path.exists(hhc) and os.path.exists(target_name + ".hhp"):
            cmd = f'"{hhc}" "{target_name}.hhp"'

    if cmd:
        try:
            print(f"Running HTML Help Workshop compiler on {target_name}.hhp ...\n")
            # split into argv list for safe execution
            argv = shlex.split(cmd)
            proc = subprocess.run(argv, shell=False, capture_output=True, text=True)
            if proc.stderr:
                print(proc.stderr.strip())
            if proc.stdout:
                print(proc.stdout.strip())
            print(f'Help Viewer file "{target_name}.chm" created.')
        except Exception as e:
            print(f"Failed to run command '{cmd}': {e}")
    else:
        print("Neither FreePascal's chmcmd.exe nor Microsoft HTML Help Workshop's hhc.exe found.")
        print(f"Please compile {target_name}.hhp manually.")

    # end of compile_chm()


def create_help_project_file(
    target_name: str, 
    title: str, 
    default_topic: str, 
    html_list: list
) -> None:
    """
    Create a help project file (`{target_name}.hhp`) 
    with the given title and default topic.
    """
    try:
        help_project_fh = open(target_name + ".hhp", "w", encoding="utf-8", newline="\n")
        if help_project_fh:
            hph = HELP_PROJECT_HEADER.format(
                target = target_name, 
                title = title, 
                default_topic = default_topic)
            help_project_fh.write(hph)
            
            for it in html_list:
                # add filenames of the generated html files to the help project file
                help_project_fh.write(it + "\n")

            print()
            # footer of help project file (*.hhp)
            help_project_fh.write(HELP_PROJECT_FOOTER)
            # close help project file
            help_project_fh.close()
            print(f'Help project file "{target_name}.hhp" created.\n')

    except Exception as e:
        print(f"Failed to write to help project file or adjust html files: {e}")
    # end of create_help_project_file()


def split_markdown_by_headers(
    readme_path: str = "README.md",
    target_name: str = "help",
    css_path: str = "",
    title: str = "Help",
    default_topic: str = "",
    out_dir: str = "README_parts",
    encoding: str = "utf-8",
    use_shell: bool = False
) -> None:
    """
    Read `readme_path` line-by-line. Whenever a line starts with "# ", "## " or "### ",
    close the previous output file (if any) and open a new UTF-8 encoded file for writing.

    Filenames use per-level counters (each level starts at 01) separated with underscores.
    After each file is closed, optionally execute `command_template` for that file.
    Use `{file}` or `{path}` in the template to insert the file path.

    Example command_template: "echo Created {file}"  (set use_shell=True on Windows)
    """
    if not os.path.exists(readme_path):
        raise FileNotFoundError(f"README not found: {readme_path}")

    current_fh: Optional[object] = None
    current_out_path: Optional[str] = None
    # counters for levels 1..4
    counters = [0, 0, 0, 0]
    old_level = 0

    try:
        with open(readme_path, "r", encoding=encoding, errors="replace") as fh:
            out_dir = os.path.abspath(out_dir)
            os.chdir(out_dir)
            toc_fh = open(os.path.join(out_dir, target_name + ".hhc"), "w", encoding=encoding, newline="\n")
            toc_fh.write(TOC_HEADER)
            html_list = []
            href_dict = {}
            href = ""
            line_count = 0
            for line in fh:
                # header lines beginning with #, ##, ###, or #### followed by space and header text
                # require special handling: close previous file, open new file
                m = _HEADER_RE.match(line)
                if m:
                    level = len(m.group(1))  # 1,2,3, or 4
                    indent = "\t"
                    closetag = ""

                    if 1 <= level <= 4:
                        # increment this level, reset deeper levels
                        counters[level - 1] += 1

                        # count downwards in order to get the indentation right:
                        # the deepest active level comes first and has the highest indentation.
                        for i in range(3, level - 1, -1):
                            if counters[i] > 0:
                                closetag += indent * i + "</UL>\n"
                            counters[i] = 0

                        header_text = m.group(2)
                        base_name = _sanitize_filename(header_text)

                        if base_name.endswith("_"):
                            base_name = base_name[:-1].rstrip()

                        # build numeric prefix like "01" or "01_01" or "01_01_01"
                        prefix_parts = [f"{counters[i]:02d}" for i in range(level)]
                        prefix = "_".join(prefix_parts)

                        # produce filename; if header text is empty use just prefix
                        if base_name:
                            filename = f"{prefix}_{base_name}.md"
                        else:
                            filename = f"{prefix}.md"

                        out_path = os.path.join(out_dir, filename)

                        # close previous file and run command for it
                        if current_fh:
                            current_fh.write("\n")
                            current_fh.close()
                            current_fh = None
                            if current_out_path:
                                if current_out_path.endswith(".md"):
                                    current_out_path = current_out_path[:-3].rstrip()
                                if line_count > 0:
                                    # execute pandoc.exe on the fragment of the markdown file to convert it to html
                                    convert_to_html(current_out_path, CONVERT_CMD, css_path=None, use_shell=use_shell)
                                    html_filename = os.path.basename(current_out_path + ".html")
                                    html_list.append(html_filename)
                                    href_dict[href] = html_filename

                            if toc_fh and toc_fh.writable() and current_out_path:
                                # finish the previous details
                                if line_count > 0:
                                    param = indent * (old_level+1) + '<param name="Local" value="{}.html">\n'
                                    toc_fh.write(param.format(os.path.basename(current_out_path)))
                                toc_fh.write(indent*old_level + '</OBJECT></LI>\n')
                                toc_fh.write(closetag)

                        # open new file with UTF-8 encoding for writing
                        current_fh = open(out_path, "w", encoding=encoding, newline="\n")
                        current_out_path = out_path
                        href = "#" + base_name.replace("_", "-").lower()
                        # write the header line as the first line
                        current_fh.write(line)
                        # reset line_count
                        line_count = 0

                        # after opening the partial output file it's time
                        # to write the new <UL> with the correct indentation to the toc.
                        if counters[level-1] == 1:
                            toc_fh.write(indent * (level-1) + '<UL>\n')

                        # start new details
                        toc_fh.write(indent * level + '<LI> <OBJECT type="text/sitemap">\n')
                        param = '<param name="Name" value="{}">\n'
                        toc_fh.write(indent * (level+1) + param.format(header_text))
                        
                        # preserve the current level to get the correct indentation for
                        # subsequent <LI> tags
                        old_level = level
                        continue  # header written, continue to next line

                # non-header lines: write to current file if open
                if current_fh:
                    if line.strip() != "":
                        line_count += 1
                    current_fh.write(line)
    finally:
        if current_fh:
            current_fh.write("\n")
            current_fh.close()
            current_fh = None
            if current_out_path:
                if current_out_path.endswith(".md"):
                    current_out_path = current_out_path[:-3].rstrip()

                # execute pandoc.exe on the fragment of the markdown file to convert it to html
                convert_to_html(current_out_path, CONVERT_CMD, css_path=None, use_shell=use_shell)
                html_filename = os.path.basename(current_out_path + ".html")
                html_list.append(html_filename)
                href_dict[href] = html_filename

            if toc_fh and toc_fh.writable() and current_out_path:
                # finish the last details
                param = indent * (old_level+1) + '<param name="Local" value="{}.html">\n'
                toc_fh.write(param.format(os.path.basename(current_out_path)))
                toc_fh.write(indent*old_level + '</OBJECT></LI>\n')

                # write the remaining </UL> tags
                for i in range(3, -1, -1):
                    if counters[i] > 0:
                        toc_fh.write(indent * i + '</UL>\n')
                    counters[i] = 0

                # write the counter part of TOC_HEADER
                toc_fh.write(TOC_FOOTER)

            if toc_fh:
                toc_fh.close()
                print(f'Table-of-content "{target_name}.hhc" generated.')

            # adjust hyperlinks etc. in the generated html files
            for it in html_list:
                adjust_html(it, href_dict)
                print(it)

            print()

            for link in href_dict:
                print(f"{link} -> {href_dict[link]}")

            print()

            if default_topic and href_dict.get(default_topic):
                default_topic = href_dict[default_topic]
            else:
                default_topic = html_list[0] if html_list and len(html_list) > 0 else ""

            # write help project file (*.hhp)
            create_help_project_file(target_name, title, default_topic, html_list)

            compile_chm(target_name)            

    # end of split_markdown_by_headers()



if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            prog = "md2chm",
            description = "convert simple md file into HTML Help project"
            )
        parser.add_argument("source", 
            type=argparse.FileType("r"),
            help = "File name or path of markdown to be converted")
        parser.add_argument("-t", "--target", type = str, 
            required=False, 
            default="",
            help="target name without extension")
        parser.add_argument("--title", type = str,
            required=False, 
            default = "Help",
            help = "Title of help document")
        parser.add_argument("--default_topic", type = str,
            required=False, 
            default = "",
            help = "Default topic")
        parser.add_argument("-w", "--workdir", type = pathlib.Path, 
            required=False,
            default = ".")
        parser.add_argument("--css", type = str, 
            required=False,
            default = "",
            help = "CSS file to be used in html output")
        parser.add_argument("-v", "--verbose",
            help="Erweiterte Ausgabe",
            action="store_true",
            required=False,
            default=False)

        # read all the parameters from the command line and store them in the `args` variable
        args = parser.parse_args()

        sourcefile = os.path.abspath(args.source.name)
        if (args.target):
            target_name = args.target
        else:
            target_name = pathlib.Path(sourcefile).stem

        workdir = args.workdir
        os.makedirs(workdir, exist_ok=True)

        default_topic = args.default_topic

        css_path = args.css
        if (css_path and os.path.exists(css_path)):
            css_path = f'--css="{css_path}"'
        else:
            css_path = "--standalone"

        if sourcefile and len(sourcefile) > 0:
            split_markdown_by_headers(sourcefile, 
                target_name = target_name, 
                css_path = css_path,
                title = args.title,
                default_topic = args.default_topic,
                out_dir = workdir, 
                use_shell=False)

            print("Split completed.")

    except FileNotFoundError as e:
        print(e)
