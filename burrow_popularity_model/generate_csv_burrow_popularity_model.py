import MySQLdb as sql
import numpy as np
import csv

######################################################################################

# Open database connection
db = sql.connect("localhost","root","bio123456","burrow_data" )
# prepare a cursor object using cursor() method

######################################################################################
def valid_burrow(burr):
	"""check if the burrow id is valid"""
	
	has_numbers= False
	no_special_chars= True
	
	# split string
	mylist = [burr[num] for num in xrange(0, len(burr))]
	
	# check if there are any numbers i nthe string
	if any(num.isdigit() for num in mylist): has_numbers = True
	if "+" in mylist: no_special_chars = False
	if "?" in mylist: no_special_chars = False
	if "/" in mylist: no_special_chars = False

	return has_numbers and no_special_chars


######################################################################################

def sample_complete_yearlist(filename):

	"""extracts years of sampling"""	
	
	yearlist = []
	
	# estimate the number of years sampled
	cursor = db.cursor()
	cursor.execute(""" select year(date) from """ + filename + """ where burrow_number> "" group by year(date) ;""")
	results = cursor.fetchall()
	yearlist = [row[0] for row in results]
	return yearlist


######################################################################################
def choose_approx_location(location_list):
	"""Chooses an approximate location by first removing the outliers and then taking an average of 
	the remaining locations"""
	
	avg = np.mean(location_list)
	std = np.std(location_list)
	
	for num in location_list: 
		# remove outliers
		if (num -avg) > 0.5* std: location_list.remove(num)
	return (np.mean(location_list))

###########################################################################################

def calculate_burrow_local_density(filename, final_burrlist, burr_attr, yearlist):
	
	"""extract burrow density (ONLY BURROW that have been "born" are COUNTED) around 100 sq m focal burrow 
	burrow_density has keys= burrow ids and val = dict with key = year and val = list with burrows that were
	alive around 1 km sq area around the burrow
	ALIVE definition = a burrow is considered to be born at the year where it was first reported. Death is
	considered to by the last year that it was reported. A burrow is considered to be alive between these years"""
	
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	
	##########################
	final_burrow_density ={}	
	for focalburr in final_burrlist:
		easting = burr_attr[focalburr][2]
		northing = burr_attr[focalburr][3]
		final_burrow_density[focalburr] ={}
		
		for year in yearlist:
			
			# extract all the burrows that have easting+-50 w.r.t focal burrows
			bur_filter1 = [bur1 for bur1 in burr_attr.keys() if focalburr!=bur1 and burr_attr[bur1][2]>=easting-50 and burr_attr[bur1][2]<=easting+50]
			
			# from bur_filter1 extract all the burrows that have northing+-50 w.r.t focal burrows
			bur_filter2 = [bur1 for bur1 in bur_filter1 if focalburr!=bur1 and burr_attr[bur1][3]>=northing-50 and burr_attr[bur1][3]<= northing+50]
			
			
			# from bur_filter2 extract all burrows that were alive during the year=year, (sorted(burr_act[bur1].keys()))[0] is the first year
			# (sorted(burr_act[bur1].keys()))[-1] is the last year. CHECK FOR "BORN" burrowa
			
			bur_filter3 =[bur1 for bur1 in bur_filter2 if burr_attr[bur1][4]<=year]
			
			# bur_filter3 is the final list. Do a len to find out number of alive burrow 
			final_burrow_density[focalburr][year] = len(bur_filter3) 

	return final_burrow_density

######################################################################################
def calculate_tort_local_density(filename, final_burrlist, burr_attr, yearlist):
	"""Extract tort density around 100 sq m of focal burrow when the burrow is alive. 
	Tort density is the averge(total (non unique) torts reported around 100 sq m of burrow each day the burrow was reported)"""
	
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	
	##########################
	
	final_tort_density ={}
	for focalburr in final_burrlist:
		final_tort_density[focalburr] ={}
		#tort_density={}
		#### look for days when the burrow was reported. NOTE: THIS RESULTED IN HIGH CORRELATION WITH DV
		#### NOW CALCULATING TORT DENSITY FOR ALL DAYS IN THE SEASON
		#cursor = db.cursor()
		#cursor.execute( """  select date from """ + filename + """  where Burrow_number = %s group by date ;""", (focalburr))
		#results = cursor.fetchall()
	
		#for row in results:
		#date = str(row[0])
		#splitdate = date.split("-")
		#year = int(splitdate[0])
		easting = burr_attr[focalburr][2]
		northing = burr_attr[focalburr][3]
		for year in yearlist:
			final_tort_density[focalburr][year] ={}	
			for season in seasondict.keys():
				cursor = db.cursor()
				cursor.execute( """  select date, count(distinct(Tortoise_number)) from """ + filename + """  where find_in_set(month(date), %s)>0 and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s ; """, (','.join(str(num) for num in seasondict[season]), easting-50, easting+50, northing-50, northing+50))
				results = cursor.fetchall() 
				if len(results)>0: final_tort_density[focalburr][year][season] = np.mean([row[1] for row in results])
				else: final_tort_density[focalburr][year][season] = 0
			######################################################
		"""
		for year in yearlist:
			if not final_tort_density[focalburr].has_key(year): final_tort_density[focalburr][year] ={}
			for season in seasondict.keys():
				keylist = [key for key in tort_density.keys() if int(key.split("-")[0])== year and int(key.split("-")[1]) in seasondict[season]]
				tortlist = [tort_density[date] for date in keylist]
				if len(tortlist)>0: final_tort_density[focalburr][year][season] = np.mean(tortlist)
				else: final_tort_density[focalburr][year][season] = 0
		"""
	return final_tort_density	
	
######################################################################################
def calculate_bur_distance(filename, burr_act, burr_attr, yearlist):
	
	"""considered biological year"""
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################burr_attr
	
	# stores average home range location of the torts at particular quarter of the year
	centr_dict={}
	for year in yearlist:
		centr_dict[year]={}
		for quarter in quarterdict.keys():
				
			##########################
			# Determine the average home range of tortoise sampled the particular time interval of the year
			cursor = db.cursor()
			cursor.execute(""" select UTM_easting, UTM_northing from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 ; """, (year, ','.join(str(num) for num in quarterdict[quarter])))
			results = cursor.fetchall()
			easting_location = [row[0] for row in results if row[0] >0]
			northing_location = [row[1] for row in results if row[1] > 0]
			
			if quarter==1:
				cursor = db.cursor()
				# In addition, extract all torts that have easting+-5 w.r.t focal burrows in that year (Jan-Feb of next calender year)
				cursor.execute(""" select UTM_easting, UTM_northing from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 ; """, (year+1, ','.join(str(num) for num in [1,2])))
				results = cursor.fetchall()
				for row in results:
					if row[0] > 0: easting_location.append(row[0])
					if row[1] >0 : northing_location.append(row[1])
				
			mean_easting = choose_approx_location(easting_location)
			mean_northing = choose_approx_location(northing_location)
			centr_dict[year][quarter] = [mean_easting, mean_northing]
			
	
	##########################
	bur_dist ={}
	for bur in burr_act.keys():
		bur_dist[bur]={}
		for year in burr_act[bur].keys():
			if year in yearlist:
				bur_dist[bur][year]={}
				for quarter in burr_act[bur][year].keys():
				
					# easting and northing location of the burrow
					bur_e = burr_attr[bur][3]
					bur_n = burr_attr[bur][4]
				
					if centr_dict[year][quarter][0] >0 and centr_dict[year][quarter][1] > 0 and bur_e>0 and bur_n >0: 
						bur_dist[bur][year][quarter] = (np.sqrt((bur_e - centr_dict[year][quarter][0])**2 + (bur_n - centr_dict[year][quarter][1])**2))/1000.0
					else: bur_dist[bur][year][quarter] = 'NA'
					#print year, quarter, bur_dist[bur][year][quarter], bur_e, bur_n, centr_dict[year][quarter][0], centr_dict[year][quarter][1]
	return bur_dist

######################################################################################
def calculate_sitespecific_average_climate(filename, site):
		
	"""Year divided into six season"""
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	##########################
	
	
	
	temp_raw={}
	rain_raw={}
	max_raw={}
	min_raw={}
	cursor = db.cursor()
	cursor.execute(""" select year(date), month(date), climate_temperature, climate_temp_max, climate_temp_min, climate_rainfall from """ + filename + """ group by year(date), month(date) """)
	results = cursor.fetchall()
	for row in results:
		year = row[0]
		month = row[1]
		temperature = row[2]
		temp_max = row[3]
		temp_min = row[4]
		rainfall = row[5]
		if not temp_raw.has_key(year): temp_raw[year]={}
		if not rain_raw.has_key(year): rain_raw[year]={}
		if not max_raw.has_key(year): max_raw[year]={}
		if not min_raw.has_key(year): min_raw[year]={}
		temp_raw[year][month]= temperature
		max_raw[year][month] = temp_max
		min_raw[year][month] = temp_min		
		rain_raw[year][month]= rainfall
	
	
		
	temp={}
	rain={}
	maxt={}
	mint={}
	# winter rain = mean total rain from Oct- March (10-3)
	#summer rain = mean total rain from Apr -Sept( 4-9)
	rain_winter={}
	rain_summer={}
	
	for year in temp_raw.keys():
		if not temp.has_key(year): temp[year]={}
		if not rain.has_key(year): rain[year]={}
		if not maxt.has_key(year): maxt[year]={}
		if not mint.has_key(year): mint[year]={}
		if not rain_winter.has_key(year): rain_winter[year]={}
		
		
		for season in seasondict.keys():
			avg_templist =  [val for key, val in temp_raw[year].items() if key in seasondict[season] and val is not None]
			rainlist = [val for key, val in rain_raw[year].items() if key in seasondict[season] and val is not None]
			maxlist = [val for key, val in max_raw[year].items() if key in seasondict[season] and val is not None]
			minlist = [val for key, val in min_raw[year].items() if key in seasondict[season] and val is not None]
						
			if len(avg_templist)>0: temp[year][season] = np.mean(avg_templist)	
			else: temp[year][season] = 'NA'
			if len(rainlist)>0: rain[year][season] = sum(rainlist)
			else:  rain[year][season] ='NA'
			if len(maxlist)>0: maxt[year][season] = np.mean(maxlist)
			else: maxt[year][season]="NA"	
			if len(minlist)>0: mint[year][season] = np.mean(minlist)
			else: mint[year][season]="NA"
		
		mylist1=[val for key, val in rain_raw[year].items() if key in [1,2,3] and val is not None]
		if rain.has_key(year-1):
		 	mylist2 = [val for key, val in rain_raw[year-1].items() if key in [10, 11, 12] and val is not None]
		else: mylist2=[]
		rain_winter[year] = np.mean(mylist1 + mylist2)
		rain_summer[year] = np.mean([val for key, val in rain_raw[year].items() if key in [4,5,6,7,8,9] and val is not None])
		print year, rain_winter[year] , rain_summer[year] 
		
	return temp, rain, maxt, mint, rain_winter, rain_summer
	
######################################################################################
def store_days_in_month(yearlist):

	month_length={}
	
	if len(yearlist)>0:
		min_year=min(yearlist)-1
		max_year = max(yearlist)+1
		#because year-1 and year+1 is counted as biological year
		tot_yearlist = [num for num in range(min_year, max_year+1)]
		
	
	else: tot_yearlist=[]
	#print ("calculating month class for years"), tot_yearlist
	for year in tot_yearlist:
		month_length[year]={}
		for month in range(1,13):
			cursor = db.cursor()
			cursor.execute(""" select day(last_day(%s)) ; """, (str(year)+'-'+str(month)+'-10'))
			results = cursor.fetchall()
			month_length[year][month] = results[0][0]
		
	
	return month_length
			
######################################################################################
def calculate_survey_freq_rate(filename, yearlist):
	
	"""Year divided into six season"""
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	##########################
	
	sur_freq = {}
	torts_sampled={}
	days_sampled={}
	burrow_sampled = {}
	
	for year in yearlist:
		sur_freq[year]={}
		torts_sampled[year] ={}
		days_sampled[year] ={}
		burrow_sampled[year] = {}
		for season in seasondict.keys():
				
			##########################
			#### Determine the total number of torts sampled at the site for the season
			cursor = db.cursor()
			cursor.execute(""" select count(distinct(tortoise_number)) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0; """,  (year, ','.join(str(num) for num in seasondict[season])))
			results = cursor.fetchall()
			torts_sampled[year][season]=results[0][0]
			##########################
			
			##########################
			#### Determine the total number of burrow sampled at the site for the season
			cursor = db.cursor()
			cursor.execute(""" select count(distinct(burrow_number)) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0; """,  (year, ','.join(str(num) for num in seasondict[season])))
			results = cursor.fetchall()
			burrow_sampled[year][season]=results[0][0]
			##########################
			
			
			##########################
			#### Determine the days sampled at the site for the season
			cursor = db.cursor()
			cursor.execute( """ select date from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year, ','.join(str(num) for num in seasondict[season])))
			results = cursor.fetchall()
			date_list =[row[0] for row in results]
			# sorting dates
			date_list.sort()
			# calculate the average interval between the dates sampled
			if len(date_list)>1: 
				freq_list = np.mean([abs((date_list[num]-date_list[num+1]).days) for num in xrange(len(date_list)-1)])
				# survey freq = 1/ average interval between the dates sampled
				sur_freq[year][season] = 1.0/(1.0*freq_list)
			else: sur_freq[year][season] = 0 
			days_sampled[year][season] = len(date_list)
			
			##########################
				
	
	return sur_freq, torts_sampled, burrow_sampled, days_sampled


######################################################################################
def summarize_burrow_survey(filename, final_burrlist, yearlist):
	"""Calcuate survey bias w.r.t burrow. Formula - Number of days focal burrow reported"""
	
	
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	##########################
	burrfreq = {}
	for burr in final_burrlist:
		burrfreq[burr]={}
		for year in yearlist:
			burrfreq[burr][year]={}
			for season in seasondict.keys():
				##########################
				###sample number of surveyed in the season
				cursor = db.cursor()
				cursor.execute( """ select distinct(date) from """ + filename + """ where burrow_number= %s  and year(date) = %s and find_in_set(month(date), %s)>0; """,  (burr, year, ','.join(str(num) for num in seasondict[season])))
				results = cursor.fetchall()
			
				sampled_days = [row[0] for row in results]
				# sorting dates
				sampled_days.sort()
				# calculate the average interval between the dates sampled
				if len(sampled_days)>1: 
					freq_list = np.mean([abs((sampled_days[num]-sampled_days[num+1]).days) for num in xrange(len(sampled_days)-1)])
					# tortfreq = total days when tort was reported in burrow/ average interval between the dates sampled
					burrfreq[burr][year][season] = 1.0/(1.0*freq_list)
				else:burrfreq[burr][year][season]= 0 			
				##########################
				
	return  burrfreq				

######################################################################################
def extract_burr_attr(filename):
	"""extract burrow attributes"""
	
	burr_attr ={}
	cursor = db.cursor()
	cursor.execute( """  select ucase(Burrow_number), burrow_azimuth, soil_clean, UTM_easting, UTM_northing, min(year(date)), max(year(date)), surf_text, washes_pct, surf_ruf, top_pos from """ + filename + """  where Burrow_number>"" group by burrow_number ; """)
	# execute SQL query using execute() method.
	results = cursor.fetchall()
	
	for row in results:
		burr = row[0]
		if int(row[3])>0 and int(row[4])>0 and valid_burrow(burr):
			# burr attr has = [0:azimuth, 1: soil, 2:easting, 3:northing, 4:birth year, 5:death year]
			burr_attr[burr] = [row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]]
			burr_attr[burr]  = ["NA" if num==None else num for num in burr_attr[burr] ]
			
	return burr_attr
######################################################################################

def extract_data(filename, yearlist, burr_attr):
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	
	##########################
	# extract burrow yearly activity. burr_act has keys= burrow ids and val = dict with key = year and val = list with torts that 
	# visited the burrow that year
	burr_raw ={}
	tort_tot={}
	tort_unq={}
	
	#tortlist to add in mysql command
	burrlist =  tuple(["{0}".format(tort) for tort in burr_attr.keys()])
	if len(burrlist)==1: burrlist = str(burrlist)[0:-2]+ ")"
	
	for year in yearlist:
		for season in seasondict.keys():
			cursor = db.cursor()
			cursor.execute( """  select ucase(Burrow_number), count(distinct concat(date, tortoise_number)), count(distinct(tortoise_number)) from """ + filename + """  where Burrow_number in """ + str(burrlist) + """  and Tortoise_number>""  and year(date)=%s and find_in_set(month(date), %s)>0 group by burrow_number; """,  (year, ','.join(str(num) for num in seasondict[season])))

			results = cursor.fetchall()
			for row in results:
				focalburr= row[0]
				tot_count = row[1]
				unq_count = row[2]
				
				if not tort_tot.has_key(focalburr): tort_tot[focalburr]={}
				if not tort_tot[focalburr].has_key(year): tort_tot[focalburr][year]={}
				if not tort_unq.has_key(focalburr): tort_unq[focalburr]={}
				if not tort_unq[focalburr].has_key(year): tort_unq[focalburr][year]={}
				
				tort_tot[focalburr][year][season]=  tot_count
				tort_unq[focalburr][year][season]=  unq_count
			
			
			
				
				
	#######################################
	# add zeros to missing data
	for burr in burr_attr.keys():
		if not tort_tot.has_key(burr): tort_tot[burr]={}
		if not tort_unq.has_key(burr): tort_unq[tort]={}
		for year in yearlist:
			if not tort_tot[burr].has_key(year): 
				tort_tot[burr][year]={}
				tort_unq[burr][year]={}
			for season in seasondict.keys():
				if not tort_tot[burr][year].has_key(season): 
					tort_tot[burr][year][season]= 0 
					tort_unq[burr][year][season]= 0 
	
	
	##############################
				
	return tort_tot, tort_unq
	

######################################################################################

def extract_data_loose(filename, yearlist, burr_attr):
	##########################
	seasondict={}
	seasondict[1] = [1,2]
	seasondict[2] = [3,4]
	seasondict[3] = [5,6]
	seasondict[4] = [7,8]
	seasondict[5] = [9,10]
	seasondict[6] = [11,12]
	
	##########################
	
	tort_unq_loose = {}
	for year in yearlist:
		for season in seasondict.keys():
			for burrow in burr_attr.keys():
				easting = burr_attr[burrow][2]
				northing = burr_attr[burrow][3]
				cursor = db.cursor()
				cursor.execute( """  select tortoise_number from """ + filename + """  where year(date)=%s and find_in_set(month(date), %s)>0 and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s ; """, (year, ','.join(str(num) for num in seasondict[season]), easting-5, easting+5, northing-5, northing+5))
				results = cursor.fetchall()
				tortlist = list(set([row[0] for row in results]))
				
				if not tort_unq_loose.has_key(burrow): tort_unq_loose[burrow]={}
				if not tort_unq_loose[burrow].has_key(year): tort_unq_loose[burrow][year]={}
				if len(tortlist)> 0: tort_unq_loose[burrow][year][season]= len(tortlist) 
				else: tort_unq_loose[burrow][year][season]= 0
				
	return tort_unq_loose
######################################################################################
def extract_finalbur_list(tort_tot):


	"""include only those torts that have been eported least during 2 seasons during final yearlist (excluding site that were sampled ony one year) """
	
	finalburr=[]
	for burr in tort_tot.keys():
		reportlist=[]
		for year in yearlist:
			if tort_tot[burr].has_key(year):
				for season in tort_tot[burr][year].keys():
					reportlist.append(tort_tot[burr][year][season])
		if len([num for num in reportlist if num>0]) > 1 or len(yearlist)==1: finalburr.append(burr)
	
	print ("number of final burrowa="), len(finalburr)
	
	return finalburr

######################################################################################
def check_burrow_birth(burr_act, finalbur, yearlist): 

	burrow_birth={}
	for bur in finalbur:
	
		burrow_birth[bur]={}
		birthyear = sorted(burr_act[bur].keys())[0]
		for year in yearlist:
			if year==birthyear: burrow_birth[bur][year]=1
			else: burrow_birth[bur][year]=0
	
	return burrow_birth
			
		
######################################################################################
def summarize_burrow_usage(filename, site,  yearlist, temp, rain, maxtemp, mintemp,  rain_winter, rain_summer, burr_attr, tort_tot, tort_unq, tort_unq_loose , final_burrlist, local_tort_density, local_burrow_density, sur_freq, torts_sampled, burrow_sampled, days_sampled, burrfreq):	


	##########################
	season_key={}
	season_key["winter"] =[1,6]
	season_key["spring"]=[2,3]
	season_key["summer"]=[4]
	season_key["fall"]=[5]
	##############################	
	
	for bur in final_burrlist:
		for year in yearlist:
			# do not write zeros for burrows which were are "dead" or are not "born" yet
			 if burr_attr[bur][4]<=year<=burr_attr[bur][5]:
				for season in [1,2,3,4,5,6]:
					season_name = [key for key,val in season_key.items() if season in val][0]
					elem1 = [site, bur, year, season, season_name, burr_attr[bur][0], burr_attr[bur][1], year-burr_attr[bur][4], burr_attr[bur][6], burr_attr[bur][7], burr_attr[bur][8], burr_attr[bur][9], temp[year][season], rain[year][season],  rain_winter[year], rain_summer[year], maxtemp[year][season], mintemp[year][season]]
					elem2 = [local_tort_density[bur][year][season], local_burrow_density[bur][year]]
					elem3 = [sur_freq[year][season] , torts_sampled[year][season], burrow_sampled[year][season], days_sampled[year][season], burrfreq[bur][year][season] ]
					#print bur, year, tort_tot[bur][year], tort_unq[bur][year]
					elem4 =  [tort_tot[bur][year][season], tort_unq[bur][year][season], tort_unq_loose[bur][year][season]] 
					elements = elem1 +elem2+elem3 +elem4
		
					# replace missing entries with NA
					elements = ["NA" if num=="" else num for num in elements]
					elements = ["NA" if num=="N/A" else num for num in elements]		
					writer.writerow(elements)
				
	
########################################################################################################3
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate", "FI_aggregate"]
	sites = ["BSV", "CS", "HW", "LM", "MC", "PV", "SG", "SL", "FI"]
	
	writer = csv.writer(open('tortuse_22May2015.csv','wb'))
	header = ["site", "burrow_number", "year", "season_dv", "season", "azimuth",  "soil", "age", "surf_text", "washes_pct", "surf_ruf", "top_pos", "temp_avg", "Rain_tot", "rain_winter", "rain_summer", "temp_max", "temp_min", "local_tort_density", "local_burrow_density", "survey_freq",  "torts_sampled", "burrow_sampled", "days_sampled","bur_freq", "tort_tot", "tort_unq", "tort_unq_loose"] 
	writer.writerow(header)
	for site, filename in zip(sites, files):
		print filename
		temp, rain, maxtemp, mintemp,  rain_winter, rain_summer = calculate_sitespecific_average_climate(filename,site)
		print ("temperature, rain done")
		yearlist = sample_complete_yearlist(filename)
		print ("done yearlist")
		burr_attr = extract_burr_attr(filename)
		print ("done burrow attribute")
		tort_tot, tort_unq = extract_data(filename, yearlist, burr_attr)
		tort_unq_loose = extract_data_loose(filename, yearlist, burr_attr)
		print ("done burrow use")
		final_burrlist = extract_finalbur_list(tort_tot)
		print ("done final burlist")
		#new_burrow = check_burrow_birth(burr_act, finalbur, yearlist)
		local_tort_density = calculate_tort_local_density(filename, final_burrlist, burr_attr, yearlist)
		print ("done tort density")
		local_burrow_density = calculate_burrow_local_density(filename, final_burrlist, burr_attr, yearlist)
		print ("done burrow density")
		sur_freq, torts_sampled, burrow_sampled, days_sampled  = calculate_survey_freq_rate(filename, yearlist)
		print ("done survey freq and rate")
		burrfreq = summarize_burrow_survey(filename, final_burrlist, yearlist)
		print ("burrow survey done")
		
		#burdist = calculate_bur_distance(filename, burr_act, burr_attr, yearlist)
		print ("writing data...")
		summarize_burrow_usage(filename, site,  yearlist, temp, rain, maxtemp, mintemp,  rain_winter, rain_summer, burr_attr, tort_tot, tort_unq, tort_unq_loose , final_burrlist, local_tort_density, local_burrow_density, sur_freq, torts_sampled, burrow_sampled, days_sampled, burrfreq)
		
		
