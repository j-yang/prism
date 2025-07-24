**************************************************************************;
* Program name      : su.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : Creation of sdtm.su
*
* Author            : Jimmy Yang(ktxv525)
*
* Date created      : 2024-01-04
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi,
*
* Output files      : su.sas7bdat
*
* Usage notes       :  
**************************************************************************;

%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/dev/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%procprint_indi;

/* **************************************************************************; */
/* * Derive SDTM */
/* **************************************************************************; */

/*Step 1: Get the data from RAW as needed*/
/*Example: %sdtm_init(domain=&pgmname., rawdata=raw.vs, outdata=raw_vs);*/
%sdtm_init(domain=&pgmname., rawdata=, outdata=)


/*Step 2: Main body for SDTM derivation*/
/*Please use below macro if applicable, %sdtm_epoch / %sdtm_visit / %sdtm_baseline / %sdtm_seq */  









/*Step 3: Build parent SDTM domain*/
%sdtm_build(domain=&pgmname., indata=, outdata=SDTM.&pgmname.); 

/*Step 4: Build Supplemental SDTM domain*/
%sdtm_suppxx(domain=&pgmname., indata=, outdata=, qeval_condi=, debug=Y);


%logcheck_indi;

