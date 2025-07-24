**************************************************************************;
* Program name      : faho.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.faho and sdtm.suppfaho
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sdtm.faho and sdtm.suppfaho
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

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
/*%sdtm_initfmt(rawdata=);*/

options mprint mlogic;
/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set raw.hosplog;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
	set &pgmname.0;
	studyid='D8450C00005';
	domain='FA';
	usubjid=catx('/',studyid,_subject);
	faspid=catx('-',_module,_aeno);
	falnkid=faspid;
	if _hlreas='1' then facat='HOSPITALIZATION, ELECTIVE';
	else if _hlreas='2' then facat='HOSPITALIZATION, EVENT';
	FASTRESC=faorres;
	visitnum=_visit;
	module=_module;
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
	if not missing( _HLDDEST) then
            do;
            faobj='HOSPITAL';
            fatest='Discharge destination';
            fatestcd='HLDDEST';
            if _HLDDEST='99' then faorres=_HLDDESTO;
            else faorres=putc(_HLDDEST,vformat(_HLDDEST));
            output;
            end;
	if not missing( _HLFDD) then
            do;
            faobj='HOSPITAL';
            fatest='Final Discharge Diagnosis';
            fatestcd='HLFDD';
			faorres=putc(_HLFDD,vformat(_HLFDD));
            output;
            end;
	if not missing( _HLFDDHD) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Ischemic Heart Disease';
            fatestcd='HLFDDHD';
            if _HLFDDHD='99' then faorres=_HLFDDHDO;
            else faorres=putc(_HLFDDHD,vformat(_HLFDDHD));
            output;
            end;
	if not missing( _HLFDDCA) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Cardiac Arrhythmia';
            fatestcd='HLFDDCA';
            if _HLFDDCA='99' then faorres=_HLFDDCAO;
            else faorres=putc(_HLFDDCA,vformat(_HLFDDCA));
            output;
            end;
	if not missing( _HLFDDCE) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Cerebrovascular Ev';
            fatestcd='HLFDDCE';
            if _HLFDDCE='99' then faorres=_HLFDDCEO;
            else faorres=putc(_HLFDDCE,vformat(_HLFDDCE));
            output;
            end;
	if not missing( _HLFDDOC) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Other Cardiovascular';
            fatestcd='HLFDDOC';
            if _HLFDDOC='99' then faorres=_HLFDDOCO;
            else faorres=putc(_HLFDDOC,vformat(_HLFDDOC));
            output;
            end;
	if not missing( _HLFDDBL) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Non-ICH Bleeding';
            fatestcd='HLFDDBL';
            if _HLFDDBL='99' then faorres=_HLFDDBLO;
            else faorres=putc(_HLFDDBL,vformat(_HLFDDBL));
            output;
            end;
	if not missing( _HLFDDCV) then
            do;
            faobj='HOSPITAL';
            fatest='Final Dis Diag - Other Non-CV';
            fatestcd='HLFDDCV';
            if _HLFDDCV='99' then faorres=_HLFDDCVO;
            else faorres=putc(_HLFDDCV,vformat(_HLFDDCV));
            output;
            end;
	if not missing( _HLSDD) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Secondary Diag';
            fatestcd='HLSDD';
            faorres=putc(_HLSDD,vformat(_HLSDD));
            output;
            end;
	if not missing( _HLSDDHD) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Ischemic Heart Disease';
            fatestcd='HLSDDHD';
            if _HLSDDHD='99' then faorres=_HLSDDHDO;
            else faorres=putc(_HLSDDHD,vformat(_HLSDDHD));
            output;
            end;
	if not missing( _HLSDDCA) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Cardiac Arrhythmia';
            fatestcd='HLSDDCA';
            if _HLSDDCA='99' then faorres=_HLSDDCAO;
            else faorres=putc(_HLSDDCA,vformat(_HLSDDCA));
            output;
            end;
	if not missing( _HLSDDCE) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Cerebrovascular Ev';
            fatestcd='HLSDDCE';
            if _HLSDDCE='99' then faorres=_HLSDDCEO;
            else faorres=putc(_HLSDDCE,vformat(_HLSDDCE));
            output;
            end;
	if not missing( _HLSDDOC) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Other Cardiovascular';
            fatestcd='HLSDDOC';
            if _HLSDDOC='99' then faorres=_HLSDDOCO;
            else faorres=putc(_HLSDDOC,vformat(_HLSDDOC));
            output;
            end;
	if not missing( _HLSDDBL) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Non-ICH Bleeding';
            fatestcd='HLSDDBL';
            if _HLSDDBL='99' then faorres=_HLSDDBLO;
            else faorres=putc(_HLSDDBL,vformat(_HLSDDBL));
            output;
            end;
	if not missing( _HLSDDCV) then
            do;
            faobj='HOSPITAL';
            fatest='Mjr Sec Diag - Other Non-CV';
            fatestcd='HLSDDCV';
            if _HLSDDCV='99' then faorres=_HLSDDCVO;
            else faorres=putc(_HLSDDCV,vformat(_HLSDDCV));
            output;
            end;
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive EPOCH */ 
/*%sdtm_epoch(indata=&domain., outdata=&domain., domain= &domain., debug=N);*/

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.1, domain=&domain.);

/*To derive VISIT */ 
%sdtm_visit(indata = &domain.1, outdata=&domain.2);

/*To derive Baseline Flag for Findings Domains */ 
/*%sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/
/*%sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set &domain.2;
  FASEQ=FAHOSEQ;
run;

%trimvarlen(dsin=final_sdtm, dsout=final_sdtm); 

%let nobs=%count_obs(final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = , debug=Y);

****Check and update if anything need manually update****;
data final_supp;
  set final_supp;
run;

%let nobs=%count_obs(final_supp);
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

