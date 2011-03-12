import math
import types

import wx
from wx.html import HtmlEasyPrinting
from wx import Printout, PrintData, PAPER_LETTER, PrintDialogData
from wx import Printer as wxPrinter, MessageBox, PrintPreview, PrintDialog
#import  wx.lib.printout as  printout
from wx.lib.printout import PrintTable, PrintTableDraw, SetPrintout

class SongPrinter():
    def __init__(self, frame):
        self.frame = frame
        self.printer_config = wx.PrintData()
        self.printer_config.SetPaperId(wx.PAPER_LETTER)
        self.printer_config.SetOrientation(wx.LANDSCAPE)
        self.prt = EOPrintTable(self.frame, num_regions=3)

    def _setupData(self, data):
        data.sort(
            lambda a, b: cmp(
                a[0].lower().replace('the ','').strip(), 
                b[0].lower().replace('the ','').strip(), 
            )
        )
        new_data = []
        for val in data:
            new_data.append([val[0], val[1]])

        header = ['artist', 'song'] 

        self.prt.data = new_data
        self.prt.set_column = [1.2,1.2]
        self.prt.label = header
        self.prt.SetHeader("Song Printout")
        self.prt.SetFooter("Page No ", type="Num")

    def Print(self, data):
        self._setupData(data)
        self.prt.Print()

    def Preview(self, data):
        self._setupData(data)
        self.prt.Preview()

    def PageSetup(self):
        "This function handles displaying the Page Setup window and retrieving the user selected options."
        config_dialog = wx.PageSetupDialog(self.frame)   #replaces PrintDialog
        config_dialog.GetPageSetupData()
        print self.printer_config        
        config_dialog.ShowModal()
        self.printer_config = config_dialog.GetPageSetupData()
        print self.printer_config
        config_dialog.Destroy()
        self.prt.SetPrintConfig(self.printer_config)


class EOPrintTableDraw(PrintTableDraw):

    fitcache = {}

    def SetDefaults(self):
        # Number of pages per page
        self.num_regions = self.parent.num_regions
        PrintTableDraw.SetDefaults(self)

    def AdjustValues(self):
        PrintTableDraw.AdjustValues(self)
        self.region_margin = 20
        self.colwidth = self.column[-1] - self.column[0] + self.region_margin
        #print "self.column:", self.column
        #print "self.column_align:", self.column_align
        #print "self.num_regions:", self.num_regions

    def OutCanvas(self):
        print "PrintTableData.OutCanvas"
        self.AdjustValues()
        self.SetPointAdjust()

        self.y_start = self.ptop_margin + self.vertical_offset
        self.y_end = self.parent.page_height * self.pheight - self.pbottom_margin + self.vertical_offset

        self.SetPrintFont(self.label_font)

        x, y = self.DC.GetTextExtent("W")
        self.label_space = y

        self.SetPrintFont(self.text_font)

        x, y = self.DC.GetTextExtent("W")
        self.space = y

        if self.total_pages is None:
            print "Initializing printout."
            self.GetTotalPages()    # total pages for display/printing

        self.data_cnt = self.page_index[self.page-1] * self.num_regions

        self.draw = True
        self.PrintHeader()
        self.PrintFooter()
        for i in range(self.num_regions):
            self.OutPage(i)

    def GetTotalPages(self):
        print "Real Get Total Pages"
        self.data_cnt = 0
        self.draw = False
        self.page_index = [0]

        cnt = 0
        while 1:
            test = self.OutPage()
            self.page_index.append(self.data_cnt)
            if  test == False:
                break
            cnt = cnt + 1

        self.total_pages = math.ceil(float(cnt + 1) / float(self.num_regions))
        print "TOTAL:", self.total_pages

    def OutPage(self, regnum=0):
        newpage = True
        self.y = self.y_start
        self.end_x = self.column[-1]

        if self.data_cnt < len(self.data):  # if there data for display on the page
            if self.label != []:        # check if header defined
                self.PrintLabel(regnum)
        else:
            return False


        for i in range(len(self.data)):
            val = self.data[i]
            try:
                row_val = self.data[self.data_cnt]
            except:
                self.FinishDraw(regnum)
                return False

            if not self.fitcache.has_key(i):
                max_y = self.PrintRow(row_val, False, regnum=regnum)       
                # test to see if row will fit in remaining space
                test = max_y + self.space
                if test > self.y_end:
                    fits = False
                else:
                    fits = True
                self.fitcache[i] = fits
            else:
                #print "Cached: %s" % i
                fits = self.fitcache[i]

            if not fits and not newpage:
                break

            #self.ColourRowCells(max_y-self.y+self.space, regnum)       # colour the row/column
            max_y = self.PrintRow(row_val, True, regnum=regnum)      # row fits - print text
            self.DrawGridLine(regnum)     # top line of cell
            self.y = max_y + self.space

            if self.y > self.y_end:
                break

            self.data_cnt = self.data_cnt + 1
            newpage = False

        self.FinishDraw(regnum)

        if self.data_cnt == len(self.data):    # last value in list
            return False

        return True

    def PrintLabel(self, regnum):
        self.pt_space_before = self.label_pt_space_before   # set the point spacing
        self.pt_space_after = self.label_pt_space_after

        self.LabelColorRow(self.label_colour, regnum)
        self.SetPrintFont(self.label_font)

        self.col = 0
        max_y = 0
        for vtxt in self.label:
            self.region = self.column[self.col+1] - self.column[self.col]
            self.indent = self.column[self.col] + (regnum * self.colwidth)

            self.align = wx.ALIGN_LEFT

            max_out = self.OutTextRegion(vtxt, True)
            if max_out > max_y:
                max_y = max_out
            self.col = self.col + 1

        self.DrawGridLine(regnum)     # top line of label
        self.y = max_y + self.label_space

    def LabelColorRow(self, colour, regnum):
        brush = wx.Brush(colour, wx.SOLID)
        self.DC.SetBrush(brush)
        height = self.label_space + self.label_pt_space_before + self.label_pt_space_after
        start_x = self.column[0] + (regnum * self.colwidth)
        self.DC.DrawRectangle(start_x, self.y,
                              self.end_x-self.column[0]+1, height)

    def ColourRowCells(self, height, regnum):
        if self.draw == False:
            return

        col = 0
        for colour in self.column_bgcolour:
            cellcolour = self.GetCellColour(self.data_cnt, col)
            if cellcolour is not None:
                colour = cellcolour

            brush = wx.Brush(colour, wx.SOLID)
            self.DC.SetBrush(brush)
            self.DC.SetPen(wx.Pen(wx.NamedColour('WHITE'), 0))

            start_x = self.column[col] + (regnum * self.colwidth)
            width = self.column[col+1] - start_x + 2 
            self.DC.DrawRectangle(start_x, self.y, width, height)
            col = col + 1

    def PrintRow(self, row_val, draw = True, align = wx.ALIGN_LEFT, startcol=0, regnum=0):
        self.SetPrintFont(self.text_font)

        self.pt_space_before = self.text_pt_space_before   # set the point spacing
        self.pt_space_after = self.text_pt_space_after

        self.col = 0 
        max_y = 0

        #print "-------------"
        #print "ROWVAL:", row_val

        for vtxt in row_val:
            if not isinstance(vtxt,types.StringTypes):
                vtxt = str(vtxt)
            self.region = self.column[self.col+1] - self.column[self.col]
            #self.indent = self.column[self.col]
            self.indent = self.column[self.col] + (regnum * self.colwidth)

            #print "Self.Col:", self.col
            #print "COLWIDTH:", self.colwidth
            #print "Regnum:", regnum
            #print "Self.Region:", self.region
            #print "Self.Indent:", self.indent
            #print "vtxt:", vtxt
            #print "Draw:", draw
            self.align = self.column_align[self.col]

            fcolour = self.column_txtcolour[self.col]       # set font colour
            celltext = self.GetCellTextColour(self.data_cnt, self.col)
            if celltext is not None:
                fcolour = celltext      # override the column colour

            self.DC.SetTextForeground(fcolour)

            max_out = self.OutTextRegion(vtxt, draw)
            if max_out > max_y:
                max_y = max_out
            self.col = self.col + 1
        return max_y

    def FinishDraw(self, regnum=0):
        self.DrawGridLine(regnum)     # draw last row line
        self.DrawColumns(regnum)      # draw all vertical lines

    def DrawGridLine(self, regnum=0):
        if self.draw == True \
        and len(self.column) > 2:    #supress grid lines if only one column
            try:
                size = self.row_line_size[self.data_cnt]
            except:
                size = self.row_def_line_size

            if size < 1: return

            try:
                colour = self.row_line_colour[self.data_cnt]
            except:
                colour = self.row_def_line_colour

            self.DC.SetPen(wx.Pen(colour, size))

            y_out = self.y
#            y_out = self.y + self.pt_space_before + self.pt_space_after     # adjust for extra spacing
            start_x = self.column[0] + (regnum * self.colwidth)
            end_x = self.end_x + (regnum * self.colwidth)
            self.DC.DrawLine(start_x, y_out, end_x, y_out)

    def DrawColumns(self, regnum=0):
        if self.draw == True \
        and len(self.column) > 2:   #surpress grid line if only one column
            col = 0
            for val in self.column:
                try:
                    size = self.column_line_size[col]
                except:
                    size = self.column_def_line_size

                if size < 1: continue

                try:
                    colour = self.column_line_colour[col]
                except:
                    colour = self.column_def_line_colour

                indent = val + (regnum * self.colwidth)

                self.DC.SetPen(wx.Pen(colour, size))
                self.DC.DrawLine(indent, self.y_start, indent, self.y)
                col = col + 1


class EOPrintTable(PrintTable):
    table = None
#    def __init__(self, *args, **kwds):
    def __init__(self, parent, num_regions=1):
        PrintTable.__init__(self, parent)
        self.num_regions = num_regions

    def SetPrintConfig(self, data):
        self.pageSetupData = data
        self.printData = self.pageSetupData.GetPrintData()

    def DoDrawing(self, DC):
        print "self.PrintTable.DoDrawing"
        size = DC.GetSize()
        DC.BeginDrawing()
        
        if self.table is None:
            print "Initializing EOPrintTableDraw"
            self.table = EOPrintTableDraw(self, DC, size)
        else:
            self.table.DC = DC

        table = self.table
        table.data = self.data
        print "Datalen:", len(table.data)
        table.set_column = self.set_column
        table.label = self.label
        table.SetPage(self.page)
        print "Page:", self.page

        if self.preview is None:
            table.SetPSize(size[0]/self.page_width, size[1]/self.page_height)
            table.SetPTSize(size[0], size[1])
            table.SetPreview(False)
        else:
            if self.preview == 1:
                table.scale = self.scale
                table.SetPSize(size[0]/self.page_width, size[1]/self.page_height)
            else:
                table.SetPSize(self.pwidth, self.pheight)

            table.SetPTSize(self.ptwidth, self.ptheight)
            table.SetPreview(self.preview)

        table.OutCanvas()
        self.page_total = table.total_pages     # total display pages

        DC.EndDrawing()

        self.ymax = DC.MaxY()
        self.xmax = DC.MaxX()

        self.sizeh = size[0]
        self.sizew = size[1]

    def Preview(self):
        print "Print Preview!---------->"
        data = wx.PrintDialogData(self.printData)
        printout = SetPrintout(self)
        self.preview = wx.PrintPreview(printout, None, data)
        if not self.preview.Ok():
            wx.MessageBox("There was a problem printing!", "Printing", wx.OK)
            return

        self.preview.SetZoom(110)        # initial zoom value
        frame = wx.PreviewFrame(self.preview, self.parentFrame, "Print preview")

        frame.Initialize()
        if self.parentFrame:
            frame.SetPosition(self.preview_frame_pos)
            frame.SetSize(self.preview_frame_size)
        frame.Show(True)

def testPrinter():
    app = wx.PySimpleApp()
    frame = wx.Frame(None)
    somedata = """ This is
a sample Document!!

Wee

Yay
"""
    p = Printer(frame)

    p.PreviewText(somedata, "FOO!")
    app.MainLoop()

def testPrintTable():
    app = wx.PySimpleApp()
    frame = wx.Frame(None)
    somedata = []
    for i in range(500):
        somedata.append(['foo_%s' % i, 'bar_%s' % i])

    p = SongPrinter(frame)

    p.Preview(somedata)
    #p.Print(somedata)
    app.MainLoop()

if __name__ == "__main__":
    testPrintTable()
