"""Calendario local en español, sin dependencias adicionales."""
import calendar
from datetime import date
import customtkinter as ctk

MONTHS = ('Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre')


class CalendarPicker(ctk.CTkToplevel):
    def __init__(self, parent, variable, title='Seleccionar fecha'):
        super().__init__(parent)
        self.variable = variable
        try:
            self.selected = date.fromisoformat(variable.get())
        except ValueError:
            self.selected = date.today()
        self.year, self.month = self.selected.year, self.selected.month
        self.title(title)
        self.geometry('420x430')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        nav = ctk.CTkFrame(self, fg_color='transparent')
        nav.pack(fill='x', padx=16, pady=16)
        ctk.CTkButton(nav, text='‹', width=42, command=lambda:self.move(-1)).pack(side='left')
        self.caption = ctk.CTkLabel(nav, text='', font=ctk.CTkFont(size=19,weight='bold'))
        self.caption.pack(side='left', expand=True)
        ctk.CTkButton(nav, text='›', width=42, command=lambda:self.move(1)).pack(side='right')
        self.grid_days = ctk.CTkFrame(self, fg_color='transparent')
        self.grid_days.pack(fill='both', expand=True, padx=16)
        ctk.CTkButton(self,text='Hoy', height=38, command=lambda:self.choose(date.today())).pack(fill='x',padx=16,pady=16)
        self.render()

    def move(self, offset):
        index = self.year*12+self.month-1+offset
        year, month = index//12, index%12+1
        if 1 <= year <= 9999:
            self.year, self.month = year, month
            self.render()

    def render(self):
        self.caption.configure(text=f'{MONTHS[self.month-1]} {self.year}')
        for child in self.grid_days.winfo_children():
            child.destroy()
        for col, name in enumerate(('Lun','Mar','Mié','Jue','Vie','Sáb','Dom')):
            self.grid_days.columnconfigure(col,weight=1)
            ctk.CTkLabel(self.grid_days,text=name,text_color='#748195').grid(row=0,column=col)
        for row, week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(self.year,self.month),1):
            for col, day in enumerate(week):
                if not day:
                    continue
                value = date(self.year,self.month,day)
                ctk.CTkButton(self.grid_days,text=str(day),width=44,height=36,
                    fg_color='#F47724' if value==self.selected else '#203F78',
                    command=lambda d=value:self.choose(d)).grid(row=row,column=col,padx=2,pady=3)

    def choose(self, value):
        self.variable.set(value.isoformat())
        self.destroy()
