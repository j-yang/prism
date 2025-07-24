**************************************************************************;
* Program name      : @@program_name
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : @@purpose
*
* Author            : @@author
*
* Date created      : @@date
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : @@output
*
* Usage notes       :  
**************************************************************************;

%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/dev/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%let domain = %upcase(&pgmname.);
%procprint_indi;
*proc printto;

/* **************************************************************************; */
/* * Derive SDTM */
/* **************************************************************************; */

/*Step 1: To apply format to variables in RAW dataset*/
/*Example: %sdtm_init(domain=&pgmname., rawdata=raw.vs, outdata=raw_vs);*/

%*sdtm_initfmt(rawdata=consent);
option mprint;
%sdtm_init(domain=&pgmname.,rawdata=raw.consent,outdata=consent0);

proc format;
	value $trt
	'A' = 'E-E'
	'B' = 'P-E'
	;

	value $arm
	'E-E' = 'EPLONTERSEN-OPEN EPLONTERSEN'
	'P-E' = 'PLACEBO-OPEN EPLONTERSEN'
	;
quit;

data dm_consent;
	set consent0;
	length _subjid $200.;
	_subjid = strip(_subject);
	_siteid = strip(put(_centre,best.));
	%sdtm_dtc(invar_dat=_dsstdat0,outvar_dtc=_rficdtc);
	drop _patient;
proc sort; by _subjid _rficdtc ;
proc sort nodupkey; by _subjid ;
run;

data country;
	set raw.raw_countrycodes;
	length start label $200.;
	start = country_code;
	label = country;
	fmtname = '$country';
	keep start label fmtname;
run;

proc format cntlin=country;quit;
data dm_dm;
	set raw.dm(rename=(age=__age ageu=__ageu ethnic=__ethnic sex = __sex
					race1 = __race1 race4 = __race4
						race5 = __race5 race6 = __race6 race7 = __race7
raceoth = __raceoth ));
	length _subjid $200.;
	_subjid = subject;
	_country = put(substr(_subjid,2,2),$country.);
	if _country = 'China' then _country = 'CHN';
	else putlog  "WAR" "NING: Country is not China for subject" subject;
	_age = __age;
	if not missing(_age) then _ageu = 'YEARS';
	if __ethnic = 'C41222' then _ethnic = 'NOT HISPANIC OR LATINO';
	if __sex = 'C20197' then _sex = 'M';
	else if __sex = 'C16576' then _sex = 'F';
	array race __race1 __race4 __race5-__race7 __raceoth;
	do over race;
		race = upcase(putc(race,vformat(race)));
	end;
		_race1 = __race1;
		_race4 = __race4;
		_race5 = __race5;
		_race6 = __race6;
		_race7 = __race7;
		_raceoth = __raceoth;
	if cmiss(__RACE1,__RACE4,__RACE5,__RACE6,__RACE7,__raceoth) < 4 then do;
		_race = 'MULTIPLE';

	end;
	else if cmiss(__race1,__race4,__race5,__race6,__race7) = 4 then do;
		_race = coalescec(__race1,__race4,__race5,__race6,__race7);
	end;

	%sdtm_dtc(invar_dat=brthdat,outvar_dtc=_brthdtc);
	%sdtm_dtc(invar_dat=vis_dat,outvar_dtc=_visitdtc);	
	keep _subjid _country _age _ageu _sex _brthdtc _ethnic _race _race1 _race4-_race7 _raceoth _visitdtc;
proc sort; by _subjid;
run;

data dm_dthdtc_ae;
	set raw.serae;
	length  _dthfl_ae _dthdtc_ae _subjid $200.; 
	where aesdth = 'C49488';
	_dthfl_ae = 'Y';
	%sdtm_dtc(invar_dat=aesddat,outvar_dtc=_dthdtc_ae);
	_subjid = subject;
	keep _subjid _dthfl_ae _dthdtc_ae;
proc sort; by _subjid _dthdtc_ae;
proc sort nodupkey; by _subjid;
run;

data dm_dthdtc_ds;
	set raw.ds;
	length  _dthfl_ds _dthdtc_ds _subjid $200.; 
	if putc(dsdecod,vformat(dsdecod)) = 'Death';
	_dthfl_ds = 'Y';
	%sdtm_dtc(invar_dat=dsstdat,outvar_dtc=_dthdtc_ds);
	_subjid = subject;
	keep _subjid _dthfl_ds _dthdtc_ds;
proc sort; by _subjid _dthdtc_ds;
proc sort nodupkey; by _subjid;
run;

data ec;
	set raw.ec;
	%sdtm_dtc(invar_dat=ecstdat,invar_tim=ecsttim,outvar_dtc=ecstdtc);
run;

proc sql noprint;
	create table dm_ec as
	select subject as _subjid length = 200, min(ecstdtc) as _rfxstdtc,
	max(ecstdtc) as _rfxendtc
	from ec
	where ecyn = 'C49488'
	group by subject
	order by subject;
quit;

data rfpendtc;
	set raw.ds(rename=(dsstdat = dat))
		raw.visit(rename=(vis_dat = dat))
	
		;
	keep subject dat;
run;

proc sql noprint;
	create table dm_rfpendtc as
	select distinct subject as _subjid length = 200, max(dat) as _rfpendtc
	from rfpendtc
	group by subject
	order by subject
	;
quit;

data dm_rand;
	set raw.dummy_rand;
	length  _subjid _armcd $200.;
	_subjid = subject;
	_armcd = trtcode;
	_armcd = put(_armcd,$trt.);
	keep _subjid _armcd;
proc sort; by _subjid;
run;

data ec_kit;
	set raw.ec;
	length kit $200.;
	kit = kitno;
	keep subject kit visit;
proc sort; by subject kit visit;
run;

data dummy_kit;
	set raw.dummy_kit;
	length kit $200.;
	kit = kitno;
	keep subject kit kitbthno kittypd visit; 
proc sort; by subject kit visit;
run;

data dm_actarm0;
	merge dummy_kit ec_kit;
	by subject kit visit;
	keep subject kittypd;
proc sort; by subject kittypd;
run;

data dm_actarm;
	set dm_actarm0;
	by subject kittypd;
	if last.subject;
	length _subjid _actarmcd $200.;
	if find(kittypd, 'Placebo') then _actarmcd = 'P-E';
	else if find(kittypd , 'Eplontersen') then _actarmcd = 'E-E';
	_subjid = subject;
proc sort; by _subjid;
run;

data dm_ds;
	set raw.ds;
	where dsdecod = 'C49628';
	length dsflag _subjid $200.;
	dsflag = 'Y';
	_subjid = subject;
	keep _subjid dsflag;
proc sort; by _subjid;
run;

data dm_ie;
	set raw.ie(rename=(patient=__patient));
	where module = 'IE1';
	length _subjid _patient $200.;
	_subjid = subject;
	_patient = strip(put(__patient,best.));
	if _patient = '.' then _patient = '';
	keep _subjid _patient;
proc sort; by _subjid;
run;

data final0;
	merge dm_consent(in=a) dm_dm(in=b)
			dm_rfpendtc dm_dthdtc_ds  dm_dthdtc_ae dm_ec dm_rand dm_actarm
			dm_ds dm_ie;
	by _subjid;
	if a and b;
	subjid = _subjid;
	studyid = 'D8450C00005';
	domain = "&domain.";
	usubjid = catx('/',studyid,subjid);
	rficdtc = _rficdtc;
	rfpendtc = _rfpendtc;
	rfxstdtc = _rfxstdtc;
	rfxendtc = _rfxendtc;
	rfstdtc = rfxstdtc;
	rfendtc = rfxendtc;
	dthdtc = coalescec(_dthdtc_ae,_dthdtc_ds);
	dthfl = coalescec(_dthfl_ae,_dthfl_ds);
	siteid = _siteid;
	brthdtc = _brthdtc;
	age = _age;
	ageu = _ageu;
	SEX= _SEX;
	RACE= _RACE;
	ETHNIC= _ETHNIC;
	ARMCD= _ARMCD;
	COUNTRY= _COUNTRY;
	RACE1= _RACE1;
	RACE4= _RACE4;
	RACE5= _RACE5;
	RACE6= _RACE6;
	RACE7= _RACE7;
	RACEOTH= _RACEOTH;
	PATIENT= _PATIENT;
	actarmcd = _actarmcd;
	arm = put(armcd,$arm.);
	actarm = put(actarmcd,$arm.);
	if dsflag ='Y' then armnrs = 'SCREEN FAILURE';
	if missing(patient) and dsflag ne 'Y' then armnrs = 'NOT ASSIGNED';
	if not missing(patient) and missing(actarm) then armnrs = 'ASSIGNED, NOT TREATED';	
	if actarm ne arm and missing(armnrs) then armnrs = 'UMPLANNED TREATMENT';
	module = 'DM';
	visitdtc = _visitdtc;
run;
/*Step 4: Create Main Domain Dataset*/
***final dataset****;

%sdtm_rescrn(dsin=final0, dsout=final_sdtm, debug=Y);

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
qeval_condi = if qorig="Assigned" then qeval = 'SPONSOR' , debug=Y);

****Check and update if anything need manually update****;
data final_supp;
  set final_supp;
run;
options mprint;
%let nobs=%count_obs(indata=final_supp);
%if &nobs ne 0 %then
    %do;
    %let supplabel =  Supplemental Qualifiers for %sysfunc(upcase(&domain.));
    %put &supplabel;
    ***final SUPP dataset****;
    data sdtm.supp&pgmname.(label = "&supplabel.");
      set final_supp;
      
    run;  
    %end;


/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;



