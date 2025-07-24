**************************************************************************;
* Program name      : eg.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.eg
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.EG

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx,
					  %sdtm_blfl,%sdtm_lobxfl
*
* Output files      : eg.sas7bdat
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
proc format cntlin=raw.cntlin;quit;
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata=eg);


/*Step 2: Shell for SDTM derivation*/
%sdtm_init(domain=&pgmname.,rawdata=eg,outdata=eg0i);

%macro egtest
		(test=%str('ECG Tests'),testcd=%str('EGALL'),stat=%str(''),
		res=%str(''),unit=%str(''),cat=%str(''),
		spfy=%str(egspfy=''),clsig=%str(egclsig=''));
	egtest=&test.;
	egtestcd=&testcd.;
	egstat=&stat.;
	egorres=&res.;
	egorresu=&unit.;
	egcat=&cat.;
	&spfy.;
	&clsig.;;
	output;
%mend egtest;

data _z0&domain.0a;
	set eg0i;
	length egspfy egclsig module $200.;

	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
	%sdtm_dtc(invar_dat=_egdat, invar_tim=_egtim, outvar_dtc=&domain.dtc);
	
	egmethod='12 LEAD STANDARD';
	egpos=upcase(_egpos);
	module=strip(_module);


	if _egperf in ('No' 'N') then do;
		%egtest(stat='NOT DONE');
	end;
	else if _egperf in ('Yes' 'Y') then do;
		if _ecghrmn ne . then do;
		%egtest(test=%str('ECG Mean Heart Rate'),testcd=%str('EGHRMN'),
				res=%str(strip(put(_ecghrmn,best.))),unit=%str('beats/min'),cat=%str('MEASUREMENT'));
		end;
		if _ECGPR ne . then do;
		%egtest(test=%str('PR Interval, Aggregate'),testcd=%str('PRAG'),
				res=%str(strip(put(_ECGPR,best.))),unit=%str('ms'),cat=%str('MEASUREMENT'));
		end;
		if _ECGQRS ne . then do;
		%egtest(test=%str('QRS Duration, Aggregate'),testcd=%str('QRSAG'),
				res=%str(strip(put(_ECGQRS,best.))),unit=%str('ms'),cat=%str('MEASUREMENT'));
		end;
		if _ECGQT ne . then do;
		%egtest(test=%str('QT Interval, Aggregate'),testcd=%str('QTAG'),
				res=%str(strip(put(_ECGQT,best.))),unit=%str('ms'),cat=%str('MEASUREMENT'));
		end;
		if _ECGQTCF ne . then do;
		%egtest(test=%str('QTcF Interval, Aggregate'),testcd=%str('QTCFAG'),
				res=%str(strip(put(_ECGQTCF,best.))),unit=%str('ms'),cat=%str('MEASUREMENT'));
		end;
		if _ECGRR ne . then do;
		%egtest(test=%str('RR Interval, Aggregate'),testcd=%str('RRAG'),
				res=%str(strip(put(_ECGRR,best.))),unit=%str('ms'),cat=%str('MEASUREMENT'));
		end;
		if _EGHRTM ne '' then do;
			if _EGHRTM='Normal sinus rhythm' then do;
				egtest='Sinus Node Rhythms and Arrhythmias';
				egtestcd='SNRARRY';
				egorres=upcase(_eghrtm);
			end;
			else if _EGHRTM in ('Atrial fibrillation' 'Atrial flutter') then do;
				egtest='Supraventricular Tachyarrhythmias';
				egtestcd='SPRTARRY';
				egorres=upcase(_eghrtm);
			end;
			else if _EGHRTM='Paced rhythm' then do;
				egtest='Pacemaker';
				egtestcd='PACEMAKR';
				egorres=upcase(_eghrtm);
			end;
			else if _EGHRTM='Other' then do;
				egtest='Other Heart Rythm';
				egtestcd='OTHERHR';
				egorres='OTHER HEART RHYTHM';
			end;
			egorresu='';egclsig='';
			egcat='FINDING';
			egstat='';
			egspfy=_eghrtmo;			
			output;
		end;
		if _INTP ne '' then do;
			egtest='Interpretation';
			egtestcd='INTP';
			egorres=upcase(_INTP);
			egorresu='';
			egcat='FINDING';
			egstat='';
			egspfy=_INTPR;
			egclsig=substr(_EGCLSIG,1,1);	
			output;
		end;
	end;
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
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
	visitnum=_visit;
	egstresc=egorres;
	egstresu=egorresu;
	egstresn=input(egstresc,??best.);
	proc sort ;
	by usubjid &domain.test &domain.dtc;
run;



/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

/*To derive EPOCH */ 
%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.94, domain=&domain.);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm0;
	set a0&domain.94;
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

