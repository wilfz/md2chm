# md2chm
## Convert Markdown to Compiled HTML

It's good custom to have a README.md for each github repository. With a growing project size the README.md grows as well.  
On the other hand many desktop applications need documentation in form of help files. The Windows operating system contains the help file viewer hh.exe and even other OS such as Linux distributions provide viewers for chm (Compiled Help Module / Compiled HTML Help) files.  
So why not convert existing markdown documentation into the chm format?  

This is exactly what _md2chm_ does.

## Prerequisites

- _md2chm_ is a python program, so you need a python3 interpreter on your machine.
- For the conversion from markdown to HTML you need the command line program pandoc in your PATH
- For the final compilation to .chm (Compiled HTML Module) you need either HTML Help Workshop from Microsoft installed on your machine or the command line tool chmcmd from FreePascal or Lazarus must in PATH. Each is part of the default installation of the corresponding package.
- Currently _ms2chm_ works only on Windows. Although it can probably made platform-agnostic I have not yet tackled this.  


## Usage
_md2chm_ is a command line program which needs some parameters:  
```
md2chm.py [-h] [-t TARGET] [--title TITLE] [--default_topic DEFAULT_TOPIC] [-w WORKDIR] [--css CSS] [-v] source
```

- source is the absolute or relative path of the markdown file which shoukld be converted
- TARGET is the file name (without the suffix .chm) of the Compiled HTML Module file that shall be created
- TITLE is the text of the title bar in help viewer
- DEFAULT_TOPIC ist the topic that should be initially open in TARGET.chm
- all intermediate and the final files are created in WORKDIR
- CSS path of css file to be used for html output

Depending on your Python installation it may be necessary to prepend the python interpreter's name or full path and a blank before the above command.

**Example:**  
This command creates the file *md2chm.chm* in the wordir folder:  
```
python.exe md2chm.py README.md --title "md2chm help" --target md2chm --workdir help --default_topic #usage
```


## How does it work?

- _md2chm_ breaks up a markdown source file at the markdown head lines of various levels and writes the parts into separate files in your specified workdir.
- Each such chunk of markdown is converted into a separate HTML5 file by the command line tool _pandoc_.
- The resulting html files still have to be a adjusted:
  - Links within the markdown are converted into links to the respective generated html file. 
  - External html links are explictly specified with target="_blank", so that they will be opened in the standard browser and not within the help viewer.
- (From here on, it would be principally possible to use Microsoft's HTML Help Workshop to construct - with quite some manual configuration work  - the scaffold for the final chm.  
After all the final chm file will not be much more than a collection of these HTML files, zipped, glued together and augmented with a table of content.)
- Instead of manual configuration, _md2chm_ does the scaffolding for you and writes a table of content (.hhc) file and a HTML Help Project (.hhp) file into your workdir.  
- The only remainig thing to do, is to compile that help project into the final chm file, either with the above mentioned HTML Help Workshop hhc.exe from Microsoft, or with FreePascal's chmcmd.exe.  
The good thing is, that _md2chm_ does even that for you if hhc.exe resides in "%ProgramFiles(x86)%\HTML Help Workshop\" or the location of chmcmd.exe is included in the search PATH environment variable.   
Otherwise _md2chm_ just exits after creating the table-of-content (.hhc) and project (.hhp) files and you have to invoke a suitable help compiler youself.  

## TODO:
- copy and compile images into chm
- enable script for linux
