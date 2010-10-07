#!/usr/bin/env python
# coding: utf-8
'''
apply shaded effects(http://mrdoob.com/projects/harmony/#shaded) to active path. 
'''

from gimpfu import *
from gimpcolor import RGB
import cairo
from copy import copy

cfg_desc = [
    (PF_FLOAT, "inter_precision", "interpolate precision", 1.0),
    (PF_FLOAT, "linear_precision", "linear precision", 5.0),
    (PF_INT, "maxdist", "max length of lines", 50),
    (PF_INT, "ignore_adjacent", "ignore adjacent pixels", 10),
    (PF_BOOL, "fill", "fill or selection", True),
    (PF_COLOR, "fillcolor", "fill color", RGB(0, 0, 0)),
    (PF_FLOAT, "alpha_rate", "transparency rate", 0.1),
    (PF_FLOAT, "line_width", "line width", 1.0),
]

Config = type('Config', (object,), {})
CFG=Config()

def mkpoints(points):
    '''
    input [x1,y1,x2,y2...]
    output [(x1,y1), (x2,y2) ...]
    '''
    i = 1
    length = len(points)
    while True:
        if i>length-1:
            break
        yield points[i-1], points[i]
        i+=2

def mklines(l):
    '''
    Point = (float, float)
    input [p1, p2, p3, p4...]
    output [(p1,p2,alpha), (p1, p3,alpha)...]
    '''
    length = len(l)
    i = j = 0
    maxdist = CFG.maxdist*CFG.maxdist
    while i<length:
        j = i+CFG.ignore_adjacent
        while j<length:
            p1, p2 = l[i], l[j]
            d = distance(p1, p2)
            if d<maxdist:
                yield l[i], l[j], 1-d/maxdist
            j+=1
        i+=1

def distance((x1,y1), (x2,y2)):
    dx = x1-x2
    dy = y1-y2
    return dx*dx+dy*dy

def cairo_draw(points):
    '''
    input:[(x1,y1), (x2,y2), ...]
    output:buffer
    '''
    if CFG.fill:
        format = cairo.FORMAT_ARGB32
    else:
        format = cairo.FORMAT_A8
    surface = cairo.ImageSurface(format, CFG.width, CFG.height)
    ctx = cairo.Context(surface)
    #ctx.set_antialias(CFG.antialiase)
    #ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.set_line_width(CFG.line_width)

    color = CFG.fillcolor
    for p1,p2,alpha in mklines(points):
        alpha = alpha*CFG.alpha_rate
        if CFG.fill:
            ctx.set_source_rgba(color.red,color.green,color.blue,alpha)
        else:
            ctx.set_source_rgba(0,0,0,alpha)
        ctx.move_to(*p1)
        ctx.line_to(*p2)
        ctx.stroke()
    return surface.get_data()

def between(n, l, r):
    '''
    return True if n between l and r
    '''
    return (n-l)*(r-n)>0

def interpolate(stroke):
    points, closed = stroke.interpolate(CFG.inter_precision)
    #points, closed = stroke.points
    points = list(mkpoints(points))
    print 'input points', len(points)
    # do linear interpolate on points
    unit = CFG.linear_precision
    result = []
    for p in points:
        if not result:
            result.append(p)
            continue
        prev = result[-1]

        x1,y1=prev
        x2,y2=p
        nx,ny=x1,y1

        # vector prev->p
        dx =x2-x1;
        dy =y2-y1;
        d = math.sqrt(dx*dx+dy*dy)
        if d==0:
            continue
        if d<=unit:
            result.append(p)
            continue
        mx = unit*dx/d
        my = unit*dy/d
        while True:
            nx += mx
            ny += my
            result.append( (nx, ny) )
            if not between(nx, x1, x2) and not between(ny, y1, y2):
                break

        result.append(p)
    print 'result points', len(result)
    return result, closed

def harmony(img, layer, *args):
    '''
    plugin function
    see register call for config parameters.
    '''
    CFG.width,CFG.height = img.width,img.height
    names = [name for _,name,_,_ in cfg_desc]
    for k,v in zip(names, args):
        setattr(CFG, k, v)

    # get an active path
    path = pdb.gimp_image_get_active_vectors(img)
    if not path:
        pdb.gimp_message('no active path')
        return

    # make an undo group
    pdb.gimp_image_undo_group_start(img)

    if CFG.fill:
        # create a new layer
        drawable = gimp.Layer(img, 'harmony', CFG.width,CFG.height, RGBA_IMAGE, 100, NORMAL_MODE)
        img.add_layer(drawable, 0)
    else:
        # create new selection
        drawable = img.selection

    # use custom interpolate method to generate points
    # a path contains multiple strokes, stroke contains control points
    allpoints = []
    for stroke in path.strokes:
        points, closed = interpolate(stroke)
        allpoints += points

    # use cairo draw to a memory buffer
    buf = cairo_draw(allpoints)

    # copy buf to pixel range
    rgn = drawable.get_pixel_rgn(0,0,CFG.width,CFG.height,True,True)
    rgn[0:CFG.width,0:CFG.height] = str(buf)

    # make the change to take effect
    drawable.flush()
    drawable.merge_shadow()
    drawable.update(0,0,CFG.width,CFG.height)

    # flush all screen display
    pdb.gimp_displays_flush()

    # finish undo group
    pdb.gimp_image_undo_group_end(img)

# tell gimp about our plugin
register(
    # unique name
    "python_fu_harmony",    
    # short description
    N_("apply shaded effects"),
    # long description
    "apply shaded effects to current path.",
    u"yi huang",
    u"yi huang",
    "2010",
    # menu path
    "<Image>/Filters/harmony...",
    # enable on what image format
    "*",
    # arguments spec
    copy(cfg_desc),
    [],
    # the function
    harmony
)

# have to call this
main()
