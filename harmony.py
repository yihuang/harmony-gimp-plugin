#!/usr/bin/env python
# coding: utf-8
from gimpfu import *
import cairo

def cairo_draw(w, h, points):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surface)

    lines = list(combine(points))
    for p1,p2 in lines:
        d = distance(p1,p2)
        if d<1000:
            ctx.set_source_rgba(0,0,0,(1-d/1000)*0.1)
            ctx.move_to(*p1)
            ctx.line_to(*p2)
            ctx.stroke()
    return surface.get_data()

def mkpoints(points):
    i = 1
    length = len(points)
    while True:
        if i>length-1:
            break
        yield points[i-1], points[i]
        i+=2

def combine(l):
    length = len(l)
    i = j = 0
    while i<length:
        j = i+1
        while j<length:
            yield l[i], l[j]
            j+=1
        i+=1

def distance((x1,y1), (x2,y2)):
    dx = x1-x2
    dy = y1-y2
    return dx*dx+dy*dy

def draw_line(drawable, (x1,y1), (x2,y2), alpha):
    #pdb.gimp_context_set_opacity(alpha)
    pdb.gimp_paintbrush_default(drawable, 4, [x1,y1,x2,y2])
    #pdb.gimp_pencil(drawable, 4, [x1,y1,x2,y2])

def do_stroke(drawable, points):
    lines = list(combine(points))
    print 'point count', len(points), 'lines count', len(lines)
    for p1,p2 in lines:
        d = distance(p1,p2)
        if d<1000:
            draw_line(drawable, p1, p2, (1-d/1000)*10)

def between(n, l, r):
    '''
    return True if n between l and r
    '''
    return (n-l)*(r-n)>0

def interpolate(stroke):
    points, closed = stroke.interpolate(10.0)
    points = list(mkpoints(points))
    print 'input points', len(points)
    # do linear interpolate on points
    unit = 2
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
        mx = unit*dx/d
        my = unit*dy/d
        while True:
            nx += mx
            ny += my
            result.append( (nx, ny) )
            if not between(nx, x1, x2) or not between(ny, y1, y2):
                break

        result.append(p)
    print 'result points', len(result)
    return result, closed

def harmony(img, layer):
    path = pdb.gimp_image_get_active_vectors(img)
    if not path:
        pdb.gimp_message('no active path')
        return

    pdb.gimp_image_undo_group_start(img)

    allpoints = []
    for stroke in path.strokes:
        points, closed = interpolate(stroke)
        allpoints += points

    w,h = layer.width,layer.height
    buf = cairo_draw(layer.width, layer.height, allpoints)
    rgn = layer.get_pixel_rgn(0,0,w,h,True,True)
    rgn[0:w,0:h] = str(buf)
    layer.flush()
    layer.merge_shadow()
    layer.update(0,0,w,h)

    pdb.gimp_displays_flush()
    pdb.gimp_image_undo_group_end(img)

register(
        "python_harmony",
        "",
        "",
        u"yihuang",
        u"yihuang",
        "2010",
        "<Image>/Filters/harmony...",
        "*",
        [
        ],
        [],
        harmony,
        )

main()
