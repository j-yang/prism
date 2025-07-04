**************************************************************************;
* Program name      : v_sdtm.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/work_val/program
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

* Macros used       : %setup, %localsetup, %procprint_indi, %logcheck_indi
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
%let domain=%scan(&PGMNAME,2, "_");
%procprint_indi;

/* **************************************************************************; */
/* * Derive SDTM */
/* **************************************************************************; */

/*Step 1: Get the data from RAW as needed, apply all pre-defined format*/
/*Example: %v_initfmt(rbsds=visit1, rawdata=visit); please use rbsds to specify the tab name in RDES*/
%v_initfmt (rbsds=, rawdata=);


/*Step 2: Main body for SDTM derivation*/
/*Please use below macro if applicable, %v_isodtc / %v_mdy / %v_blfl / %v_lobxfl / %v_epoch / %v_visit / %v_seq */  
%v_
*Convert **DAT tp **DTC using is8601 format, use in the data step;
/*Example: % v_isodtc(datin=lbdat, timin=lbtim, dtcout=lbdtc, datin_type=C, timin_type=C, debug=N); */
%v_isodtc(datin=, timin=, dtcout=);

*Calculate DY based on DTC and SDTM.DM.RFSTDCT;
/*Example: % v_mdy(datain=final, dataout=final, dtcin=lbdtc, dyout=lbdy, debug=N ); */
%v_mdy(datain=, dataout=, dtcin=, dyout=);


*Map with SDTM.TV to get visit and visitdy;
%v_visit(datain=, dataout=)

*Derive Baseline Flag;
/*Example: % v_blfl(domain=lb, datain=final, dataout=final, sortby=%str(usubjid lbcat lbtestcd lbdtc), groupby=%str(usubjid lbcat lbtestcd), debug=N); */
%v_blfl(domain=, datain=, dataout=, sortby=%str(), groupby=%str());
%v_lobxfl(domain=, datain=, dataout=, sortby=%str(), groupby=%str());


*Derive EPOCH;
/*Example: % epoch(datain=final, dataout=final, dtcvar=lbdtc, debug=N); */
%epoch(datain=, dataout=, dtcvar=);


*Derive seq var;
/*example: %v %v_seq(domain=faae, datain=final, seqvar=faseq, startseq=1, debug = N);*/
%v_seq(domain=, datain=, seqvar=);





/* **************************************************************************; */
/* * Output SDTM and SUPPSDTM */
/* **************************************************************************; */
/*Build parent SDTM domain and SUPPSDTM domain if applicable, output lib is QCSDTM*/
%v_gensdtm(domain=, datain=, trim=Y);
/*check log*/
%logcheck_indi;


