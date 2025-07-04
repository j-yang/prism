**************************************************************************;
* Program name      : @@program_name
*
* Program path      : root/cdar/d693/d6935c00003/ar/dr1/adam/dev/program
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

* Macros used       : %setup, %localsetup, %m_adam_attrib
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

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Merge supp to main domain*/
%*m_adam_mergesupp(dsin= , );


/*Step 2: Analysis dataset creation*/











/*Step 3: Assign attributes to dataset and variables*/;
*%m_adam_attrib(specSheet = &domain.
            ,inads      = final
            ,outads     = adam.&domain.
            ,headRow    =12
            ,prtDupkey  =Y 
            ,debug      =N 
);


/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

