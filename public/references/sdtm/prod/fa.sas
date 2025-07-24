**************************************************************************;
* Program name      : fa.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.fa
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.ATTRCMD, RAW.STOPR, RAW.LIVERDI, RAW.LIVERRF, RAW.MER, RAW.NYHAHF

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : fa.sas7bdat
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
%put &domain.;
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata=ATTRCMD STOPR LIVERDI LIVERRF MER NYHAHF INJSTRC DEATHEVT HOSPLOG);

/*Step 2: Shell for SDTM derivation*/

%macro test
		(test=%str('ATTR Diagnosis'),testcd=%str('DIAGNOS'),cat=%str('Disease History'),scat=%str(''),
		obj=%str(''),res=%str(''),unit=%str(''),eval=%str(''),spfy=%str(''),where=%str()
		,sires=%str(&domain.orres)
		);
	if &where. then do;
		&domain.test=&test.;
		&domain.testcd=&testcd.;
		&domain.cat=&cat.;
		&domain.scat=&scat.;
		&domain.obj=&obj.;
		&domain.orres=&res.;
		&domain.orresu=&unit.;
		&domain.stresc=&sires.;
		&domain.eval=&eval.;
		&domain.spfy=&spfy.;
		
		output;
	end;
%mend test;

*ATTRCMD;
%sdtm_init(domain=&pgmname.,rawdata=ATTRCMD,outdata=ATTRCMD0i);

data __z0&domain.0a;
	length faspfy faeval   $200.;
	set ATTRCMD0i;
	
	&domain.grpid=strip(_module)||'-'||strip(put(_MODULE_O,z4.))||":"||strip(put(_LINE,z2.));
	&domain.spid=strip(_module)||'-'||strip(put(_LINE,z2.));
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);

	array ccny $200 ATTRCMF ATTRCMM ATTRCMS ATTRCMO  ATTRPNF ATTRPNM ATTRPNS ATTRPNO ;
	array ccnyo _CMFHSPFA _CMFHSPMO _CMFHSPSI _CMFHSPOT  _PNFHSPFA _PNFHSPMO _PNFHSPSI _PNFHSPOT ;

	array cc $200 module ATTRCMOT ATTRPNOT;
	array cco _module _CMFHOTH _PNFHOTH;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
	do j=1 to dim(ccny);
		*ccny(j)=substr(ccnyo(j),1,1);
		ccny(j)=ccnyo(j);
	end;

	%test(obj=%str('Date of Transthyretin-Mediated Amyloid Cardiomyopathy Diagnosis'),res=%str(_ATTRDDAT)
		,where=%str(_ATTRDDAT ne ''));
	%test(obj=%str('Any ATTR_CM Genotyping'),res=%str(_ATTRGYN)
		,where=%str(_ATTRGYN ne ''));
	%test(obj=%str('Date of ATTR_CM Genotyping'),res=%str(_ATTRGDAT)
		,where=%str(_ATTRGDAT ne ''));
	%test(obj=%str('TTR Mutation Identified'),res=%str(_ATTRMRES)
		,where=%str(_ATTRMRES ne ''));
	%test(obj=%str('Type of ATTR_CM'),res=%str(_ATRESCAT)
		,where=%str(_ATRESCAT ne ''));
	%test(obj=%str('Hereditary Mutation'),res=%str(_ATHESPEC),spfy=%str(_ATHEROTH)
		,where=%str(_ATHESPEC ne ''));
	%test(obj=%str('Any Novo Mutation'),res=%str(_ATNMYN),spfy=%str(_ATNMSPEC)
		,where=%str(_ATNMYN ne ''));
	%test(obj=%str('Present a Mixed Phenoty With ATTR_PN'),res=%str(_ATPNYN)
		,where=%str(_ATPNYN ne ''));
	%test(obj=%str('Date of ATTR_PN Genotyping'),res=%str(_ATPNDDAT)
		,where=%str(_ATPNDDAT ne ''));
	%test(test=%str('Date of Onset of ATTR_PN Symptoms'),testcd=%str('ONSETPN'),cat=%str('Disease History')
		,obj=%str('Date of Onset of ATTR_PN Symptoms'),res=%str(_ATPNSDAT)
		,where=%str(_ATPNSDAT ne ''));
	%test(obj=%str('Any Family History of ATTR_CM'),res=%str(_ATFHYN)
		,where=%str(_ATFHYN ne ''));
	%test(obj=%str('Any Family History of ATTR_PN'),res=%str(_PNFHYN)
		,where=%str(_PNFHYN ne ''));
	%test(test=%str('Date of Onset of ATTR_CM Symptoms'),testcd=%str('ONSETCM'),cat=%str('Disease History'),
		obj=%str('Date of Transthyretin-Mediated Amyloid Cardiomyopathy Symptoms Onset'),res=%str(_ATTRSDAT)
		,where=%str(_ATTRSDAT ne ''));
	
run;

data _z0&domain.0a;
	set __z0&domain.0a;

	if missing(FAORRES) or FAOBJ^='Any Family History of ATTR_CM'  
		then call missing(ATTRCMF,ATTRCMM, ATTRCMS, ATTRCMO,ATTRCMOT);
	if missing(FAORRES) or FAOBJ^='Any Family History of ATTR_PN'  
		then call missing(ATTRPNF ,ATTRPNM, ATTRPNS, ATTRPNO,ATTRPNOT);
run;



*STOPR;
%sdtm_init(domain=&pgmname.,rawdata=STOPR,outdata=STOPR0i);

data _z0&domain.0b;
	length faspfy faeval   $200.;
	set STOPR0i;	
	
	&domain.spid=strip(_module)||'-'||strip(put(_LINE,z3.));
	&domain.grpid=strip(_module)||'-'||strip(put(_LINE,z3.));
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);

	array cc $200 module  ;
	array cco _module  ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;

	%test(test=%str('AE Reported'),testcd=%str('AEREPO'),cat=%str(_STOPRCAT),
		obj=%str('AE Reported'),res=%str(substr(_STAEYN,1,1)),eval=%str(_STOPEVA),spfy=%str(_STOPEOTH)
		,where=%str(_STAEYN ne ''));
	%test(test=%str('AE Reported Number'),testcd=%str('AEREPON'),cat=%str(_STOPRCAT),
		obj=%str('AE Reported'),res=%str(strip(put(_STAENUM,best.))),eval=%str(_STOPEVA),spfy=%str(_STOPEOTH)
		,where=%str(_STAENUM ne .));
	%test(test=%str('Resolved'),testcd=%str('RESOLV'),cat=%str(_STOPRCAT),
		obj=%str('Resolved'),res=%str(substr(_RESOLV,1,1)),eval=%str(_STOPEVA),spfy=%str(_STOPEOTH)
		,where=%str(_RESOLV ne ''));
	%test(test=%str('Outcome'),testcd=%str('OUTCOM'),cat=%str(_STOPRCAT),
		obj=%str('Outcome'),res=%str(_STOPOUT),eval=%str(_STOPEVA),spfy=%str(_STOPEOTH)
		,where=%str(_STOPOUT ne ''));
	
run;

*LIVERDI;
%sdtm_init(domain=&pgmname.,rawdata=LIVERDI,outdata=LIVERDI0I);

data _z0&domain.0c;
	length faspfy faeval   $200.;
	set LIVERDI0I;	
	
	&domain.spid=strip(put(_FACSPID,best.));

	array cc $200 module LIVDSPEC famethod ;
	array cco _module  _LIVDSPEC _FACMETHD;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
	if _FAPERF in ('N' 'No') then fastat='NOT DONE';
	%sdtm_dtc(invar_dat=_FACDAT, invar_tim=, outvar_dtc=fadtc);

	%test(test=%str('Liver Diagnostic Investigation Results'),testcd=%str('LIVERDI'),cat=%str('LIVER FUNCTION'),
		obj=%str('IMPAIRED LIVER FUNCTION'),res=%str(_LIVDIRES)
		,where=%str(_SUBJECT ne ''));
	
run;


*LIVERRF;
%sdtm_init(domain=&pgmname.,rawdata=LIVERRF,outdata=LIVERRF0I);

data _z0&domain.0d;
	length faspfy faeval   $200.;
	set LIVERRF0I;	
	
	&domain.spid=strip(put(_MHCSPID,best.));

	array cc $200 module livrspec ;
	array cco _module  _livrspec;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
	%sdtm_dtc(invar_dat=_LIVDAT, invar_tim=, outvar_dtc=fadtc);
	%sdtm_dtc(invar_dat=_LIVRSDAT, invar_tim=, outvar_dtc=fastdtc);
	%sdtm_dtc(invar_dat=_LIVREDAT, invar_tim=, outvar_dtc=faendtc);
	faenrtpt=upcase(_LIVREFP);
	faentpt=fadtc;

	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('LIVER RISK FACTORS/LIFE STYLE EVENTS'),
		obj=%str(_LIVRF),res=%str(substr(_LIVRFOCC,1,1))
		,where=%str(_LIVRF ne ''));	
run;

*MER;
%sdtm_init(domain=&pgmname.,rawdata=MER,outdata=MER0i);

data _z0&domain.0e;
	length DEFSPEC  faspfy faeval  $200.;
	set MER0i;	
	
	&domain.spid='AE-'||strip(put(_AENO,best.));

	array cc $200 module MEDEV MEAE;
	array cco _module  _MEDEV _MEAE;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;

	array ccu $200 DESCAT DESCPE ;
	array ccuo _DESCAT  _DESCPE ;

	do j=1 to dim(ccu);
		ccu(j)=upcase(ccuo(j));
	end;

	DEFSPEC=coalescec(upcase(_DEFSPEC),_MEDEF);
	%sdtm_dtc(invar_dat=_FACMDAT, invar_tim=, outvar_dtc=fadtc);

	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('MEDICATION ERROR'),
		obj=%str('Stage of Error (Storage)'),scat=%str('STORAGE'),res=%str(_SEOSTOR)
		,where=%str(_seostor ne ''));
	%test(test=%str('Specify'),testcd=%str('SPECIFY'),cat=%str('MEDICATION ERROR'),
			obj=%str('Medication Error Occurrence'),scat=%str(''),res=%str(_MEOCCUR)
			,where=%str(_MEOCCUR ne ''));
	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('MEDICATION ERROR'),
			obj=%str('Stage of Error (Administration)'),scat=%str('ADMINISTRATION'),res=%str(_SEOADM)
			,where=%str(_SEOADM ne ''));
	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('MEDICATION ERROR'),
			obj=%str('Stage of Error (Prep for Admin)'),scat=%str('PREP FOR ADMIN'),res=%str(_SEOPADM)
			,where=%str(_SEOPADM ne ''));	
	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('MEDICATION ERROR'),
			obj=%str('Stage of Error (Dispensing)'),scat=%str('DISPENSING'),res=%str(_SEODISP)
			,where=%str(_SEODISP ne ''));	
run;

*NYHAHF;
%sdtm_init(domain=&pgmname.,rawdata=NYHAHF,outdata=NYHAHF0i);

proc  format ;
	value $nyh
		'No limitation'='NYHA CLASS I'
		'Slight limitation'='NYHA CLASS II'
		'Marked limitation'='NYHA CLASS III'
		'Unable to carry out'='NYHA CLASS IV'
		;
	invalue nyhn
		'No limitation'=1
		'Slight limitation'=2
		'Marked limitation'=3
		'Unable to carry out'=4
		;
run;

data _z0&domain.0f;
	length faspfy faeval   $200.;
	set NYHAHF0i;
	&domain.spid=strip(_module)||'-'||strip(put(_LINE,z2.));


	array cc $200 module  ;
	array cco _module   ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;


	%sdtm_dtc(invar_dat=_VIS_DAT, invar_tim=, outvar_dtc=visitdtc);
	%sdtm_dtc(invar_dat=_VIS_DAT, invar_tim=, outvar_dtc=fadtc);

	%test(test=%str('New York Heart Association Class'),testcd=%str('NYHACLS'),cat=%str('NYHA'),
		obj=%str('HEART FAILURE'),scat=%str(''),res=%str(PUT(_NYHAHF,$nyh.))
		,where=%str(_subject ne ''));
	
run;

/*origin code FACE, DEATHEVT*/
%sdtm_init(domain=&pgmname.,rawdata=DEATHEVT,outdata=DEATHEVT0i);

data _z0&domain.0ad;
	length module $200.;
	set DEATHEVT0i;
	
	module=strip(_module);
	&domain.lnkid=strip(module)||'-'||strip(put(_aeno,best.));
	&domain.spid=strip(module)||'-'||strip(put(_aeno,best.));
	&domain.lnkgrp='AE-'||strip(put(_aeno,best.));
	%sdtm_dtc(invar_dat=_aesddat,outvar_dtc=fadtc);
	%test(test=%str('Event Associated with Hospitalization'),testcd=%str('HOSPEV'),
		cat=%str('DEATH EVENT'),obj=%str(_CETERM),
		res=%str(_HOSPEV),sires=%str(_HOSPEV)
		,where=%str(_HOSPEV ne '')
		);
	%test(test=%str('Primary Cause of Death'),testcd=%str('PRCDTH'),
		cat=%str('DEATH EVENT'),obj=%str(_CETERM),
		res=%str(ifc(_vassclso ne '', trim(left(upcase(_vassclso))), upcase(_vasscls))),
		sires=%str(upcase(_vasscls))
		,where=%str(_VASSCLS ne '')
		);
	%test(test=%str('Primary Cause of Death, Non-Cardiovascular'),testcd=%str('PRCDTHNC'),
		cat=%str('DEATH EVENT'),obj=%str(_CETERM),
		res=%str(ifc(_nvassclo ne '', trim(left(upcase(_nvassclo))), upcase(_nvasscls))),
		sires=%str(upcase(_nvasscls))
		,where=%str(_NVASSCLS ne '')
		);
	
run;

/*INJSTRC, origin code FAAE.sas, Jihao Yang*/
%sdtm_init(domain=&pgmname.,rawdata=INJSTRC,outdata=INJSTRC0I);

data _z0&domain.0aj;
	set INJSTRC0I;
	FASPID = CAT('AE','-',_AENO);
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=fadtc);
	module = _module;
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=visitdtc);

	facat = 'INJECTION SITE REACTIONS';
	faobj = 'ONSET';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _ISRONTM;
	FASTRESC =CATS(_ISRONTM);
	output;

	faobj = 'RESOLUTION';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _ISRTIMRS;
	FASTRESC =CATS(_ISRTIMRS);
	output;
	
	FASCAT = 'SYMPTOMS';
	faobj = 'PRURITIS';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRPRUR;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'RASH';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRRASH;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'ERYTHEMA';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRERYT;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'SWELLING/EDEMA/INDURATION';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRWEDIN;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'PAIN/DISCOMFORT/TENDERNESS';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRPADTR;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'HEMATOMA AND BRUISING';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRHEBRU;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'BLEEDING';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRBLEED;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'WARMTH';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRWARM;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'OTHER, SPECIFY';
	FATESTCD = 'SPECIFY';
	FATEST = 'Specify';
	FAORRES = strip(upcase(_isroth));
	FASTRESC =faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SEVERITY SYMPTOM';
	FATESTCD = 'SPECIFY';
	FATEST = 'Specify';
	FAORRES = _isrshsv;
	FASTRESC =faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SEVERITY GRADE';
	FATESTCD = 'SEV';
	FATEST = 'Severity/Intensity';
	FAORRES = _isrhssg;
	FASTRESC = faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SYMPTOM';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _isronths;
	FASTRESC = CATS(faorres);
	output;

/*	call missing(fascat);*/
/*	faobj = 'AFFECTED AREA';*/
/*	FATESTCD = 'DIAM';*/
/*	FATEST = 'Diameter';*/
/*	faorres = put(_isrdaa,best.);*/
/*	fastresc = faorres;*/
/*	faorresu = _isrdaau;*/
/*	fastresn = _isrdaa;*/
/*	fastresu = faorresu;*/
/*	output;*/
run;

data  _z0&domain.0aj;
	set _z0&domain.0aj;
	where faorres>'';
run;


/*HOSPLOG, origin code FAHO.sas, Zifan Guo*/
/*Need to pay attention whether FASTRESC impute correctly*/

%sdtm_init(domain=&pgmname.,rawdata=HOSPLOG,outdata=HOSPLOG0i);

data _z0&domain.0ah;
	set HOSPLOG0i;

	faspid=catx('-',_module,_aeno);
	if _hlreas IN ('1' 'Elective hospitalization') then facat='HOSPITALIZATION, ELECTIVE';
	else if _hlreas IN ('2' 'AE/SAE') then facat='HOSPITALIZATION, EVENT';
	module=_module;
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
	if not missing( _HLDDEST) then
            do;
            faobj='HOSPITAL';
            fatest='Discharge destination';
            fatestcd='HLDDEST';
            if _HLDDEST IN ('99' 'Other' ) then faorres=_HLDDESTO;
            else faorres=putc(_HLDDEST,vformat(_HLDDEST));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDD) then
            do;
            faobj='HOSPITAL';
            fatest='Final Discharge Diagnosis';
            fatestcd='HLFDD';
			faorres=putc(_HLFDD,vformat(_HLFDD));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDHD) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Ischemic Heart Disease';
            fatestcd='HLFDDHD';
            if _HLFDDHD IN ('99' 'Other' ) then faorres=_HLFDDHDO;
            else faorres=putc(_HLFDDHD,vformat(_HLFDDHD));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDCA) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Cardiac Arrhythmia';
            fatestcd='HLFDDCA';
            if _HLFDDCA IN ('99' 'Other' ) then faorres=_HLFDDCAO;
            else faorres=putc(_HLFDDCA,vformat(_HLFDDCA));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDCE) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Cerebrovascular Ev';
            fatestcd='HLFDDCE';
            if _HLFDDCE IN ('99' 'Other' ) then faorres=_HLFDDCEO;
            else faorres=putc(_HLFDDCE,vformat(_HLFDDCE));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDOC) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Other Cardiovascular';
            fatestcd='HLFDDOC';
            if _HLFDDOC IN ('99' 'Other' ) then faorres=_HLFDDOCO;
            else faorres=putc(_HLFDDOC,vformat(_HLFDDOC));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDBL) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Non-ICH Bleeding';
            fatestcd='HLFDDBL';
            if _HLFDDBL IN ('99' 'Other' ) then faorres=_HLFDDBLO;
            else faorres=putc(_HLFDDBL,vformat(_HLFDDBL));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLFDDCV) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Other Non-CV';
            fatestcd='HLFDDCV';
            if _HLFDDCV IN ('99' 'Other' ) then faorres=_HLFDDCVO;
            else faorres=putc(_HLFDDCV,vformat(_HLFDDCV));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDD) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Secondary Diag';
            fatestcd='HLSDD';
            faorres=putc(_HLSDD,vformat(_HLSDD));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDHD) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Ischemic Heart Disease';
            fatestcd='HLSDDHD';
            if _HLSDDHD IN ('99' 'Other' ) then faorres=_HLSDDHDO;
            else faorres=putc(_HLSDDHD,vformat(_HLSDDHD));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDCA) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Cardiac Arrhythmia';
            fatestcd='HLSDDCA';
            if _HLSDDCA IN ('99' 'Other' ) then faorres=_HLSDDCAO;
            else faorres=putc(_HLSDDCA,vformat(_HLSDDCA));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDCE) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Cerebrovascular Ev';
            fatestcd='HLSDDCE';
            if _HLSDDCE IN ('99' 'Other' ) then faorres=_HLSDDCEO;
            else faorres=putc(_HLSDDCE,vformat(_HLSDDCE));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDOC) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Other Cardiovascular';
            fatestcd='HLSDDOC';
            if _HLSDDOC IN ('99' 'Other' ) then faorres=_HLSDDOCO;
            else faorres=putc(_HLSDDOC,vformat(_HLSDDOC));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDBL) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Non-ICH Bleeding';
            fatestcd='HLSDDBL';
            if _HLSDDBL IN ('99' 'Other' ) then faorres=_HLSDDBLO;
            else faorres=putc(_HLSDDBL,vformat(_HLSDDBL));
			FASTRESC=faorres;
            output;
            end;
	if not missing( _HLSDDCV) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Other Non-CV';
            fatestcd='HLSDDCV';
            if _HLSDDCV IN ('99' 'Other' ) then faorres=_HLSDDCVO;
            else faorres=putc(_HLSDDCV,vformat(_HLSDDCV));
			FASTRESC=faorres;
            output;
            end;
run;

data _null_;
	set _z0fa0ah;
	if fastresc ne faorres then put 'STAR_C' 'HECK: ' 'HOSPITAL, FASTRESC need to update';
run;
/*Step 3: Main body for SDTM derivation*/


%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,_subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;

data a0&domain.01;
	set _z0&domain.0:;
	%sdtm_studyid;
	visitnum=_visit;
	*fastresc=faorres;
	fastresu=faorresu;
	*if facat='NYHA' then fastresn=input(fastresc,??nyhn.);
	if find(faobj,'date','i')=0 then fastresn=input(fastresc,??best.);
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
	%sdtm_dy(invar_dtc=&domain.stdtc,outvar_dy=&domain.stdy);
	%sdtm_dy(invar_dtc=&domain.endtc,outvar_dy=&domain.endy);
	proc sort ;
	by usubjid &domain.cat &domain.test &domain.obj ;
run;



/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 

/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

/*To derive EPOCH */ 
%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
*%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
*%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.92, domain=&domain.);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm0;
	set a0&domain.92;
	drop _:;
run;

%sdtm_rescrn(dsin=final_sdtm0, dsout=final_sdtm, debug=Y);


%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = %str(if qorig='Assigned' then qeval = 'SPONSOR'), debug=Y);

****Check and update if anything need manually update****;
data final_supp;
  set final_supp;
run;

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

