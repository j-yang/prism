**************************************************************************;
* Program name      : ae.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ae
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : ae.sas7bdat
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

option mprint;
/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

proc format ;
    value  $nyfmt
        "C49487"="N"
        "C49488"="Y"
    ;
    value $relfmt
        "C49487"="UNLIKELY AE CAUSED BY IP"
        "C49488"="REASONABLE POSSIBILITY AE CAUSED BY IP"
     ;
run;

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%*sdtm_initfmt(rawdata=);


/*Step 2: Shell for SDTM derivation*/
data aeonly;
    set raw.ae;
    where aeyn^="C49487";
/*     if aeterm ne "" then output aeonly; */
/*     else  */
/*         do; */
/*         title "Programming Notes:"; */
/*         file print; */
/*         put _page_; */
/*         put "Err" "or: data issue in missing aeterm: " subject; */
/*         end; */
run;

proc sort data=aeonly;
    by subject aeno aeterm;
run;

data serae;
    set raw.serae;
*drop aedis;
run;

proc sort data=serae;
    by subject aeno aeterm;
run;

data &pgmname._raw;
    merge aeonly(in=a) serae;
    by subject aeno aeterm;
    if a;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

data &pgmname.1;
    set &pgmname.0;

    studyid=_study;
    DOMAIN="&domain.";
    usubjid=cat( _study,  '/',   _subject);
    
    if _AENO ne . then AESPID=cats('AE-',strip(put(_AENO, best.))); 
    AETERM=_aeterm;
    AELLT=strip(_llt_name);
    AELLTCD=_llt_code;
    AEDECOD=strip(_pt_name);
    AEPTCD=_pt_code;
    AEHLT=strip(_hlt_name);
    AEHLTCD=_hlt_code;
    AEHLGT=strip(_hlgtname);
    AEHLGTCD=_hlgtcode;
    AECAT = ifc(_AECATOCC = 'C49488', upcase(vvalue(_AECAT)), '');
    
    AEBODSYS=strip(_soc_name);
    AEBDSYCD=_soc_code;
    AESOC=strip(_soc_name);
    AESOCCD=_soc_code;
    

/*  AESEV = max(upcase(putc(_aesev,vformat(_aesev))), upcase(putc(_aec01sev,vformat(_aec01sev))),  upcase(putc(_aec02sev,vformat(_aec02sev))));*/
    AESEV = upcase(putc(_AESEVMAX,vformat(_AESEVMAX)));
    AESER = substr(upcase(putc(_AESER,vformat(_AESER))),1,1);
    AEACN =  ifc(_AEACN='4', 'DRUG WITHDRAWN', upcase(put(_AEACN,$AEACN.)));
    AEREL = put(_AEREL, $relfmt.);
    AEOUT = upcase(putc(_AEOUT,vformat(_AEOUT)));
    
    if not missing(_aescong) then AESCONG=put(_aescong,$NY.);
    if not missing(_aesdisab) then AESDISAB=put(_aesdisab,$NY.);
    if not missing(_aesdth) then AESDTH=put(_aesdth,$NY.);
    if not missing(_aeshosp) then AESHOSP=put(_aeshosp,$NY.);
    if not missing(_aeslife) then AESLIFE=put(_aeslife,$NY.);
    if not missing(_aesmie) then AESMIE=put(_aesmie,$NY.);
    AECONTRT = put(_AECONTRT,$NY.);

    %sdtm_dtc(INVAR_DAT=_aestdat,OUTVAR_DTC=&pgmname.STDTC );
    %sdtm_dtc(INVAR_DAT=_aeendat,OUTVAR_DTC=&pgmname.ENDTC );
    %sdtm_dy(INVAR_DTC = &pgmname.stdtc , OUTVAR_DY = &pgmname.stdy );
    %sdtm_dy(INVAR_DTC = &pgmname.endtc , OUTVAR_DY = &pgmname.endy );
    
    IP = _IP;
    AEWD = put(_AEDIS, $nyfmt.);
    MEDDRAV = _MEDDRA_V;
    aerelnst=ifc(_AESMEDCA EQ 'C49488', 'CAUSED BY OTHER MEDICATION ' || UPCASE(TRIM(_AESMED)), '');

    if not missing(_aecaussp) then SAECAUSP=substr(vvalue(_aecaussp),1,1);
    SAESP=strip(_aesp);

    %sdtm_dtc(INVAR_DAT=_aesddat ,INVAR_TIM= ,OUTVAR_DTC=SAEDDTC );
    DTHCAUS1=strip(_dthcaus1);
    DTHCAUS2=strip(_dthcaus2);
    if not missing(_aesautop) then SAEAU=put(_aesautop,$nyfmt.); 
    %sdtm_dtc(INVAR_DAT=_aesdidat ,INVAR_TIM= ,OUTVAR_DTC=SAEDIDTC );
    %sdtm_dtc(INVAR_DAT=_aesdat ,INVAR_TIM= ,OUTVAR_DTC=SAEDTC );
    %sdtm_dtc(INVAR_DAT=_aeshodat ,INVAR_TIM= ,OUTVAR_DTC=SAEHODTC );
    %sdtm_dtc(INVAR_DAT=_aesiadat ,INVAR_TIM= ,OUTVAR_DTC=SAEIADTC );
    
run;

data ae2;
    length tmp $2000.;
    set &pgmname.1;
    tmp=compbl(trim(left(cat(of _aedesc:))));
    
    length aedesc01-aedesc11 $200;
    informat aedesc01-aedesc11 $200.;
    format aedesc01-aedesc11 $200.;
    retain cs 200;
    
    array wraps{11} $200 aedesc01-aedesc11;
    if length(tmp)<=cs then 
        do; 
        tsval=trim(left(tmp)); j=1; 
        end;
    else
        do;
        c=1; length=length(tmp); j=1;
        do until(c>length);
            c=c+verify(substr(tmp, c), ' ')-1;
            if c+cs>length then l=length+1-c;
            else
                do;
                l=cs; break=0;
                    do i=(c+cs-1) to c-1 by -1 until(break);
                    if substr(tmp, i+1, 1)=' ' 
/*                         | */
/*                        (substr(tmp, i, 1)='-' & substr(tmp, i+1, 1) ne '-')  */
                       then 
                       do; break=1; l=i+1-c; end;
                    end;
                end;
            wraps{j}=substr(tmp, c, l); 
            c=c+l; j=j+1;
        end;
        end;
    if j>1 then j=j-1;
	module = 'AE SAE';
	aeterm = upcase(aeterm);
	if missing(aedesc01) then aedesc01 = tsval;
run; 

/*To derive EPOCH */ 
%sdtm_epoch(indata=ae2, outdata=ae3, domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=ae3, domain=ae);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;

%sdtm_rescrn(dsin=ae3, dsout=final_sdtm, debug=Y);

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
	qeval_condi = if qorig="Assigned" then qeval = 'SPONSOR', debug=Y);
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

