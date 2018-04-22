#!/usr/bin/python

'''
 Plot.py

 A simple command line data plotting program with support for algebraic expressions and the scipy.signal and numpy.fft modules.

 Data  is read from column formatted file or stdin.  Leading lines of text are treated as comments and displayed by the --contents switch.

 Data columns can be referenced as column0, column1, etc., or by labels corresponding to words or quoted strings read from the last comment line.

 Caveat: to use the full python allowed syntax to specify the data to be graphed, the column labels should be valid as names of variables in python

 For example, and input file might contain

          This is my data
          a b c
          0.1 0.2 0.3
          0.2 0.4 0.6
          0.3 0.7 1.0
          ... etc


 The data can be plotted by commands lines such as

     ./Plot.py  datafile --x a --y column1 (c-b)/100

     ./Plot.py  datafile --y 'abs(fft.fft(column0))**2'

     ./Plot.py  datafile --y 'abs(fft.rfft(b-np.median(b)))**2' --x 'fft.rfftfreq( len(b), 1./1.E6)'



 Author and copyright:

   Mitchell C Nelson, PhD
   April 16, 2018


This software is provided free for use, with no guarantee of suitability for any purpose whatsoever.



'''

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

import scipy.signal as signal
import numpy.fft as fft

import shlex

if (sys.version_info < (3,6)):
    from collections import OrderedDict


# ----------------------------------------------

def readfile( fp ):

    # read comments and data
    # last comment used as labels for the columns
    comments = []
    rows = []
    cols = []
    labels = []

    npos = fp.tell()
    line = fp.readline()
    #print( 'line %s'%line )

    while line:
        line = line.strip()
        if not line:
            break
        
        try:
            rows.append( [ float(s) for s in line.split() ] )

        except:
            if not rows:
                comments.append( line )
            else:
                fp.seek(npos)
                break                

        npos = fp.tell()
        line = fp.readline()
        #print( 'line %s'%line )

    #convert to columns
    if rows:
        cols = list( map(list, zip(*rows) ) )
        
    # find labels if provided
    if comments:
        s = comments[-1]
        if s.startswith('#'): s = s[1:].strip()
        if s.startswith('labels'): s = s[1:].strip()
        labels = shlex.split( s )
   
    return cols, comments, labels

# --------------------------------------------

def gety( a_string, a_dict ):

    try:
        y = a_dict[ a_string ]
        return y
    except:
        pass
    
    for key, val in a_dict.items():
        try:
            exec( key + '= np.array(val)' )
        except:
            pass
    
    if (sys.version_info < (3,6)):
        exec( 'y = '+a_string )
    else:
        exec( 'y = '+a_string, locals(), globals() )
        
    return y

# ----------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument('datafile', nargs='?',
                    type=argparse.FileType('r'),
                    default = sys.stdin,
                    help = 'Input file' )

parser.add_argument( '--output' )

parser.add_argument('--y', nargs='+',
                    help='Choose the y data columns, see keys listed by --contents.' )

parser.add_argument('--x',
                    help='Choose the x data column, see keys listed by --contents.' )

parser.add_argument('--xmax', type=float )
parser.add_argument('--xmin', type=float )
parser.add_argument('--ymax', type=float )
parser.add_argument('--ymin', type=float )

parser.add_argument('--xlabel' )
parser.add_argument('--ylabel' )
parser.add_argument('--title' )

parser.add_argument( '--contents', action='store_true' )
parser.add_argument( '--fft', action='store_true' )
parser.add_argument( '--samplerate', type=float, default=1. )

args = parser.parse_args()

# ----------------------------------------------

cols, comments, labels = readfile( args.datafile )
nrows = len(cols[0])

# Create a dictionary to reference the data
if (sys.version_info < (3,6)):
    data = OrderedDict()
else:
    data = {}

for n,c in enumerate(cols):
    data[ 'column%d'%n ] = c

if labels:
    for l, c in zip(labels,cols):
        data [ l ] = c

# -----------------------------------
# Show contents and exit
if args.contents:
    if len(comments) > 1:
        for c in comments:
            print( c )
    print( 'keys: '+', '.join(data.keys()) )
    sys.exit()
        
# -----------------------------------

if args.fft:
    f = np.fft.rfftfreq( nrows, 1./args.samplerate)

    if args.y:
        for key in args.y:
            c = gety( key, data )
            g = fft.rfft(c)
            g = g * np.conjugate( g )
            plt.plot( f[1:int(len(g))], g[1:int(len(g))].real, label=key )
    else:
        for n,c in enumerate(cols):
            g = np.fft.rfft(c)
            g = g * np.conjugate( g )
            plt.plot( f[1:int(len(g))], g[1:int(len(g))].real, label='column %d'%n )
            
else:
    if args.x:
        t = gety( args.x, data )
    else:
        t = np.linspace( 0., nrows*args.samplerate, nrows )

    if args.y:
        for key in args.y:
            c = gety( key, data )
            plt.plot( t, c, label=key )
    else:
        for n,c in enumerate(cols):
            plt.plot( t, c, label='column %d'%n )

# -----------------------------------

if not args.y or len(args.y) > 1:
    plt.legend()

if args.ylabel:
    plt.ylabel( args.ylabel )
elif args.y and len(args.y) == 1:
    if args.fft:
        plt.ylabel( '$\\rm | '+args.y[0]+' |^2$' )
    else:
        plt.ylabel( args.y )
elif args.fft:
    plt.ylabel( '$\\rm | y(f) |^2$' )

if args.xmin:
    plt.xlim( xmin=args.xmin )
if args.xmax:
    plt.xlim( xmax=args.xmax )
    
if args.ymin:
    plt.ylim( ymin=args.ymin )
if args.ymax:
    plt.ylim( ymax=args.ymax )
    
if args.xlabel:
    plt.xlabel( args.ylabel )
elif args.fft:
    plt.xlabel( 'frequency' )   
elif args.x:
    plt.xlabel( args.x )
    
if args.title:
    plt.title( args.title )
else:
    plt.title( args.datafile.name )

# -----------------------------------

if args.output:
    plt.savefig( args.output )

else:
    plt.show()
