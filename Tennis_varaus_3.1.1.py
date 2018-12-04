# Scripti tarkistaa onko vapaita tennisvuoroja kyseisella ajankohdalla

import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
import time
import sys
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#from email.MIMEMultipart import MIMEMultipart
#from email.MIMEText import MIMEText

import argparse # Easy way to handle parameters; python3 main.py 13:30 15:00 
# import bottle


viikonpaivat = {'Monday': 'maanantai', 'Tuesday': 'tiistai', 'Wednesday': 'keskiviikko', 'Thursday': 'torstai', 'Friday': 'perjantai', 'Saturday': 'lauantai', 'Sunday': 'sunnuntai'}


def tarkista_kentta(aloituspvm, aloitusaika, lopetusaika, lkm, inputday):
    
    # We should change the date url based on current datetime.datetime.now() and datetime.datetime.strftime()
    vapaat = {}
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    print ("Today is " + now.strftime("%A %d.%m.%Y %H:%M:%S"))
    viikonpaiva = viikonpaivat[aloituspvm.strftime("%A")]
    
    print ("Tarkastan loytyyko tyhjia kenttia paivamaaralla " + inputday.strftime("%Y-%m-%d") + " alkaen klo: " + aloitusaika.strftime("%H:%M"))
    print ("Lopeta painamalla Ctrl+C\n\n")
    
    interval = 1
    message = ''
    
    while interval < (lkm+1): #kuinka monen paivan osalta kentat tarkistetaan
        osoite = "https://varaukset.talintenniskeskus.fi/booking/booking-calendar?BookingCalForm[p_laji]=1&BookingCalForm[p_pvm]=" + aloituspvm.strftime("%Y-%m-%d") + "&BookingCalForm[p_pvm_interval]="+ str(interval) +"&BookingCalForm[p_pvm_custom]="+ viikonpaiva + "+" + aloituspvm.strftime("%d.%m.%Y")
        rr = requests.get(osoite)
        
        
        # Check that the page received ok
        if rr.status_code != 200:
          raise Exception("Getting failed: %s" % rr )
        
        # Then make the HTML tree out of the content
        parsed = BeautifulSoup( rr.content, "lxml" )
        
        # Then find the booking table main item
        booking_table = parsed.find( "div", { "class" : "booking-table" } )
        
        
        # Now, we need to parse the rows (html table is based on rows)
        booking_rows = booking_table.find("table").find_all("tr")
        
        for row in booking_rows:
            # Now we should process this row with some magic
        

          free_times = row.find_all( "td", { "class" : "s-avail" } )
          for free_time in free_times:
              rivi = str(free_time)
              indeksi = re.search(r'\b(kesto)\b', rivi)
              #print(indeksi.start())
              match = re.search(r'\d{4}-\d{2}-\d{2}', rivi)
              date = match.group(0)
              match = re.search(r'\d{2}:\d{2}', rivi)
              time = match.group(0)
              hh, mm = time.split(':')
              match = re.search(r'K(\d\d?)', rivi)
              kentta = match.group(0)
              vapaa_kentta = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y') + "     " + time
        
              if time >= aloitusaika.strftime("%H:%M") and time <= lopetusaika.strftime("%H:%M"):
                if vapaa_kentta not in vapaat:
                   vapaat[vapaa_kentta] = 1
                else:
                    vapaat[vapaa_kentta] += 1
                   
             
              # Append the free time to a list
              # We maybe could get the start time from the a-href element url and use that as an
              # criteria wheter to add this as "wanted time"
        
        if len(vapaat) > 0 and interval == (lkm):
            print("kentat luettu")
            return vapaat
        interval += 1

# and in the end somehow communicate that we have free times. I would guess twitter / slack would be the easiest to integrate with.

def create_message(vapaat):
    
    #print ("\nLoysin tyhjia kenttia paivamaaralla: " + list(vapaat.keys())[0])
    message = "\nLoysin tyhjia kenttia paivamaaralla: " + list(vapaat.keys())[0] + "\n"
    #print ("%5s     %s" % ("Kello", "Kenttien Lkm"))
    message = message + "   %s        %5s     %s" % ("pvm.","Kello", "Kenttien Lkm") + "\n"
    for key,value in sorted(vapaat.items()):
        #print ("%5s       %5s" % (key, value))
        message = message + ("%5s       %5s\n" % (key, value))
    print()
    print(message)
    return message


def send_mail(message):
    message_tmplt = 'Loysin tyhjia kenttia: \n\n%5s     %s' % ("Kello", "Kenttien Lkm")
    link = "https://varaukset.talintenniskeskus.fi/booking/booking-calendar"
    
    if len(message) > 0:
        fromaddr = "pasin.jaatelokioski@gmail.com"
        toaddr = "robert.ashorn@pexraytech.com"
        msg = MIMEMultipart('alternative')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Vapaita kenttia Talissa!"
         
        body = message + "\n\n" + "Varaa vuoro:\n" + link + "\n\nTerkuin\nPasi"
        msg.attach(MIMEText(body, 'plain'))
         
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr, "wazxe5-cikmyq-rYpdaj")
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        print ("Mail sent!")
        server.quit()


def main():
    print ('Pasin Jaatelokioski on auki!\n')
    
    viesti_lahetetty = ''
    # uudelleen jarjestellaamn koodi niin etta paiva ja aika kysytaan main funktiossa
    # paivamaara ja aika siirretaan tarkista_kentta funktiolle funktiota kutsuttaessa
    while True:
        try:
            aloitusaika = datetime.datetime.strptime(input('Kerro aloitusaika hh:mm muodossa: \n'), "%H:%M")
            break
            #print aloitusaika.strftime("%H:%M")
        
        except:
            print ("Anna aika muodossa hh:mm ")
     
    while True:   
        try:
            lopetusaika = datetime.datetime.strptime(input('Kerro lopetusaika hh:mm muodossa: \n'), "%H:%M")
            break
            #print aloitusaika.strftime("%H:%M")
        
        except:
            print ("Anna aika muodossa hh:mm ")
    
    
    while True: 
        try:
            inputday = datetime.datetime.strptime(input('Kerro mita paivaa halutaan tarkastella yyyy-mm-dd muodossa: \n'), "%Y-%m-%d")
            aloituspvm = inputday - timedelta(days=1)
            viikonpaiva = viikonpaivat[aloituspvm.strftime("%A")]
            break
            #print aloituspvm.strftime("%A %d.%m.%Y")
            #print str(aloituspvm)
        
        except:
            print ("Anna pvm muodossa yyyy-mm-dd ")
        
    lkm = int(input('Monenko paivan varaukset haluat tarkastaa?\n'))
    
    try:
        while True:
            vapaat = tarkista_kentta(aloituspvm, aloitusaika, lopetusaika, lkm, inputday)
            viesti = create_message(vapaat)
            if viesti != viesti_lahetetty:
                send_mail(viesti)
                viesti_lahetetty = viesti
            else:
                print('Ei muutosta edelliseen')
            time.sleep(5*60) #Funktion kutsun intervalli [s]
            
    except KeyboardInterrupt:
        print ("Pasin jaatelokioski on suljettu")
        sys.exit(0)

main()
