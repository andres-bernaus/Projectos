import datetime as dt
from dateutil.relativedelta import relativedelta

from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
#from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

allowedTimeSlots = ("antes del desayuno","despues del desayuno","antes del almuerzo","despues del almuerzo",
                    "antes de la merienda","despues de la merienda","antes de la cena","despues de la cena")

#Dada una medicion (dicc) tomo los elementos que necesito para generar la tabla
def factorize_measurement(aMeasure):
        rowDate = (aMeasure['date'].date()).strftime("%x")
        rowTimeSlot = aMeasure['timeSlot'].lower()
        rowValue = aMeasure['value']
        return rowDate,rowTimeSlot,rowValue

#Organizo los valores por dia y momento del dia (antes del desayuno, etc)
def insert_in_dictionary(aDicc,aMeasurement):
        rowDate,rowTimeSlot,rowValue = factorize_measurement(aMeasurement)
        if not (rowDate in aDicc):
            aDicc[rowDate] = {rowTimeSlot.lower() : rowValue}
        else:
            aDicc[rowDate][rowTimeSlot.lower()] = rowValue

#Genero 
def dicc_to_matrix(dicc,starting_date,end_date,row_size=9):

        result = []

        current_date = starting_date
        while current_date < end_date:
            current_date_key = current_date.strftime("%x")
            aNewRow = ["" for _ in range(row_size)]
            aNewRow[0] = current_date_key
            if aNewRow[0] in dicc:
                claves = [k.lower() for k in dicc[current_date_key].keys()]
                for idx, ts in enumerate(allowedTimeSlots):
                    if ts in claves:
                         val = dicc[current_date_key][ts]
                         aNewRow[idx+1] = val

                #aNewRow[1:] = dicc[current_date]
                #print aNewRow
            
            result.append(aNewRow)
            current_date = current_date + relativedelta(days=1)

        return result

class Measurement_table():

    def __init__(self,starting_date,ending_date,measurements):
        #Measurements es un diccionario con todas las mediciones a imprimir
        self.measurements = measurements
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.table_data = self.__build_table_data()


    #Clasifico las mediciones por dia
    def __build_table_data(self):
        dicc_por_dia = {}
        
        for aMeasure in self.measurements:
            insert_in_dictionary(dicc_por_dia,aMeasure)
        
        result = dicc_to_matrix(dicc_por_dia,self.starting_date,self.ending_date)
        
        #result = [["{}".format(i) for _ in range(9)] for i in range(10)]

        return result

    def print_table(self,filename):
        file = SimpleDocTemplate(filename,pagesize=A4)
        
        ps = ParagraphStyle('title', fontSize=8, leading=12)

        elements = []
        labels = [Paragraph("Fecha", ps),Paragraph("Antes del Desayuno", ps),Paragraph("Despues del Desayuno", ps),
                        Paragraph("Antes del Almuerzo", ps),Paragraph("Despues del Almuerzo", ps),
                        Paragraph("Antes de la Merienda", ps),Paragraph("Despues de la Merienda", ps),
                        Paragraph("Antes de la Cena", ps),Paragraph("Despues de la Cena", ps)]
        
        data = [labels] + self.table_data

        height = len(data)
        width = len(data[0])

        t=Table(data,width*[0.4*inch*2], height*[0.4*inch])
        t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                           ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                           ]))

        elements.append(t)
        # write the document to disk
        file.build(elements)

        return 0



       