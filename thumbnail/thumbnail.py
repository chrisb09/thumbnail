import os, json, signal, subprocess, time
from random import randint 

from threading import Lock

from subprocess import DEVNULL, STDOUT, check_output

unoserver = None
unoserver_lock = Lock()
unoserver_running_lock = Lock()

unoserver_interface = ""

if "UNOSERVER" in os.environ:
    host = os.environ["UNOSERVER"]
    unoserver_interface = "--interface "+host+" "
    print(unoserver_interface)

def does_unoserver_exist(verbose=False):
    fails = 0
    os.system("echo 'test' > test.txt")
    while fails<3:
        try:
            if os.system('unoconvert '+unoserver_interface+'test.txt test.pdf > /dev/null 2>&1') == 0:
                break
            time.sleep(1)
            fails += 1
        except:
            fails += 1
            time.sleep(1)
    if verbose:
        print("Unoserver exists: "+str(fails<3))
    return fails < 3
        

def open_unoserver(verbose=False):
    if verbose:
        print("open_unoserver")
    global unoserver
    if does_unoserver_exist(verbose):
        return True

    if unoserver_lock.acquire(blocking=False):
        try:
            print("start unoserver")
            unoserver = subprocess.Popen(["unoserver"])
            fails = 0
            os.system("echo 'test' > test.txt")
            while fails<30:
                try:
                    time.sleep(1)
                    if os.system('unoconvert '+unoserver_interface+'test.txt test.pdf  > /dev/null 2>&1') == 0:
                        break
                except:
                    fails += 1
        finally:
            unoserver_lock.release()
        if fails<30:
            return True
        return False
    print("Retry finding unoserver...")
    return open_unoserver()
    

def close_unoserver():
    if unoserver is not None:
        print("stop unoserver")
        os.killpg(os.getpgid(unoserver.pid), signal.SIGTERM)

        

def generate_thumbnail(input, output, options, verbose=False):
    try:
        if os.path.isfile(input):
            pass
        else:
            raise('Error!')
    except:
        print("Input File doesn't exist.")
        return False
    
    try:
        if os.path.isdir(output.rsplit('/', 1)[0]):
            pass
        elif len(output.rsplit('/', 1)) == 1:
            pass
        else:
            raise('Error!')
    except:
        print("Output directory doesn't exist.")
        return False
    
    if type(options) is dict:
        options = options
    else:
        options = {}
    
    input_ext = os.path.splitext(input)[1].replace('.', '')
    output_ext = os.path.splitext(output)[1].replace('.', '')

    def has_key(dict, key):
        return True if key in dict else False
    
    options['thumbnail'] = options['thumbnail'] if has_key(options, 'thumbnail') else True
    options['width'] = str(options['width']) if has_key(options, "width") else '300'
    options['height'] = str(options['height']) if has_key(options, "height") else '300'
    options['quality'] = str(options['quality']) if has_key(options, "quality") else '85'

    if has_key(options, 'trim'):
        if options['trim'] is True:
            options['trim'] = '-trim'
        else:
            options['trim'] = ''
    else:
        options['trim'] = ''

    if has_key(options, 'transparency'):
        if options['transparency'] is True:
            options['transparency'] = '-background transparent'
        else:
            options['transparency'] = ''
    else:
        options['transparency'] = ''

    if has_key(options, 'thumbnail'):
        if options['thumbnail']:
            imgcommand = '-extent '+options['width']+'X'+options['height']
            vidcommand = ''
        else:
            imgcommand = ''
            vidcommand = ''
    else:
        imgcommand = ''
        vidcommand = ''
    
    
    if verbose:
        print(options)

    if verbose:
        print(input_ext, output_ext)
    
    try:
        if output_ext in ['png', 'jpg', 'gif']:
            pass
        else:
            raise('Error!')
    except:
        print('Output extension is not supported.')
        return False
    
    mimedb_path = os.path.dirname(os.path.realpath(__file__)) + '/mimedb.json'
    with open(mimedb_path) as json_file:
        mimedb = json.load(json_file)

    for k in mimedb:
        if 'extensions' in mimedb[k]:
            for e in mimedb[k]['extensions']:
                if e == input_ext:
                    if k.split('/')[0] == 'image':
                        filetype = 'image'
                    elif k.split('/')[0] == 'video':
                        filetype = 'video'
                    else:
                        filetype = 'other'
                    pass
    
    try:
        filetype
    except:
        print('Input file is not supported.')
        return False
    
    if output_ext == 'pdf':
        filetype = 'image'
    
        
    if filetype == 'video':
        command = 'ffmpeg -hide_banner -loglevel error -y -i "'+input+'" -vf "thumbnail" '+vidcommand+' -frames:v 1 -vf scale=w='+options['width']+':h='+options['height']+':force_original_aspect_ratio=decrease "'+output+'"'
        if verbose:
            print(command)
        os.system(command)
    elif filetype == 'image':
        command = 'convert -thumbnail "'+options['width']+'X'+options['height']+'" '+options['trim']+' -quality '+options['quality']+' '+imgcommand+' '+options['transparency']+' "'+input+'"[0] "'+output+'"'
        if verbose:
            print(command)
        os.system(command)
    elif filetype == 'other':

        tmppath = './' + str(randint(1000, 999999)) + '.pdf'
        if open_unoserver(verbose):
            command = 'unoconvert '+unoserver_interface+'--convert-to pdf "'+input+'" "'+tmppath+'"'
            if verbose:
                print(command)
            os.system(command)

            while not os.path.exists(tmppath):
                time.sleep(0.5)

            command = 'convert -thumbnail "'+options['width']+'X'+options['height']+'" '+options['trim']+' -quality '+options['quality']+' '+imgcommand+' -gravity center '+tmppath+'[0] "'+output+'"'
            if verbose:
                print(command)
            os.system(command)
            os.remove(tmppath)
        else:
            return False
        
    return True