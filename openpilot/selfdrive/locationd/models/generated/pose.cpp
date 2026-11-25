#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_6287899668351208780) {
   out_6287899668351208780[0] = delta_x[0] + nom_x[0];
   out_6287899668351208780[1] = delta_x[1] + nom_x[1];
   out_6287899668351208780[2] = delta_x[2] + nom_x[2];
   out_6287899668351208780[3] = delta_x[3] + nom_x[3];
   out_6287899668351208780[4] = delta_x[4] + nom_x[4];
   out_6287899668351208780[5] = delta_x[5] + nom_x[5];
   out_6287899668351208780[6] = delta_x[6] + nom_x[6];
   out_6287899668351208780[7] = delta_x[7] + nom_x[7];
   out_6287899668351208780[8] = delta_x[8] + nom_x[8];
   out_6287899668351208780[9] = delta_x[9] + nom_x[9];
   out_6287899668351208780[10] = delta_x[10] + nom_x[10];
   out_6287899668351208780[11] = delta_x[11] + nom_x[11];
   out_6287899668351208780[12] = delta_x[12] + nom_x[12];
   out_6287899668351208780[13] = delta_x[13] + nom_x[13];
   out_6287899668351208780[14] = delta_x[14] + nom_x[14];
   out_6287899668351208780[15] = delta_x[15] + nom_x[15];
   out_6287899668351208780[16] = delta_x[16] + nom_x[16];
   out_6287899668351208780[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_4433323129515526623) {
   out_4433323129515526623[0] = -nom_x[0] + true_x[0];
   out_4433323129515526623[1] = -nom_x[1] + true_x[1];
   out_4433323129515526623[2] = -nom_x[2] + true_x[2];
   out_4433323129515526623[3] = -nom_x[3] + true_x[3];
   out_4433323129515526623[4] = -nom_x[4] + true_x[4];
   out_4433323129515526623[5] = -nom_x[5] + true_x[5];
   out_4433323129515526623[6] = -nom_x[6] + true_x[6];
   out_4433323129515526623[7] = -nom_x[7] + true_x[7];
   out_4433323129515526623[8] = -nom_x[8] + true_x[8];
   out_4433323129515526623[9] = -nom_x[9] + true_x[9];
   out_4433323129515526623[10] = -nom_x[10] + true_x[10];
   out_4433323129515526623[11] = -nom_x[11] + true_x[11];
   out_4433323129515526623[12] = -nom_x[12] + true_x[12];
   out_4433323129515526623[13] = -nom_x[13] + true_x[13];
   out_4433323129515526623[14] = -nom_x[14] + true_x[14];
   out_4433323129515526623[15] = -nom_x[15] + true_x[15];
   out_4433323129515526623[16] = -nom_x[16] + true_x[16];
   out_4433323129515526623[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_3663906507468251580) {
   out_3663906507468251580[0] = 1.0;
   out_3663906507468251580[1] = 0.0;
   out_3663906507468251580[2] = 0.0;
   out_3663906507468251580[3] = 0.0;
   out_3663906507468251580[4] = 0.0;
   out_3663906507468251580[5] = 0.0;
   out_3663906507468251580[6] = 0.0;
   out_3663906507468251580[7] = 0.0;
   out_3663906507468251580[8] = 0.0;
   out_3663906507468251580[9] = 0.0;
   out_3663906507468251580[10] = 0.0;
   out_3663906507468251580[11] = 0.0;
   out_3663906507468251580[12] = 0.0;
   out_3663906507468251580[13] = 0.0;
   out_3663906507468251580[14] = 0.0;
   out_3663906507468251580[15] = 0.0;
   out_3663906507468251580[16] = 0.0;
   out_3663906507468251580[17] = 0.0;
   out_3663906507468251580[18] = 0.0;
   out_3663906507468251580[19] = 1.0;
   out_3663906507468251580[20] = 0.0;
   out_3663906507468251580[21] = 0.0;
   out_3663906507468251580[22] = 0.0;
   out_3663906507468251580[23] = 0.0;
   out_3663906507468251580[24] = 0.0;
   out_3663906507468251580[25] = 0.0;
   out_3663906507468251580[26] = 0.0;
   out_3663906507468251580[27] = 0.0;
   out_3663906507468251580[28] = 0.0;
   out_3663906507468251580[29] = 0.0;
   out_3663906507468251580[30] = 0.0;
   out_3663906507468251580[31] = 0.0;
   out_3663906507468251580[32] = 0.0;
   out_3663906507468251580[33] = 0.0;
   out_3663906507468251580[34] = 0.0;
   out_3663906507468251580[35] = 0.0;
   out_3663906507468251580[36] = 0.0;
   out_3663906507468251580[37] = 0.0;
   out_3663906507468251580[38] = 1.0;
   out_3663906507468251580[39] = 0.0;
   out_3663906507468251580[40] = 0.0;
   out_3663906507468251580[41] = 0.0;
   out_3663906507468251580[42] = 0.0;
   out_3663906507468251580[43] = 0.0;
   out_3663906507468251580[44] = 0.0;
   out_3663906507468251580[45] = 0.0;
   out_3663906507468251580[46] = 0.0;
   out_3663906507468251580[47] = 0.0;
   out_3663906507468251580[48] = 0.0;
   out_3663906507468251580[49] = 0.0;
   out_3663906507468251580[50] = 0.0;
   out_3663906507468251580[51] = 0.0;
   out_3663906507468251580[52] = 0.0;
   out_3663906507468251580[53] = 0.0;
   out_3663906507468251580[54] = 0.0;
   out_3663906507468251580[55] = 0.0;
   out_3663906507468251580[56] = 0.0;
   out_3663906507468251580[57] = 1.0;
   out_3663906507468251580[58] = 0.0;
   out_3663906507468251580[59] = 0.0;
   out_3663906507468251580[60] = 0.0;
   out_3663906507468251580[61] = 0.0;
   out_3663906507468251580[62] = 0.0;
   out_3663906507468251580[63] = 0.0;
   out_3663906507468251580[64] = 0.0;
   out_3663906507468251580[65] = 0.0;
   out_3663906507468251580[66] = 0.0;
   out_3663906507468251580[67] = 0.0;
   out_3663906507468251580[68] = 0.0;
   out_3663906507468251580[69] = 0.0;
   out_3663906507468251580[70] = 0.0;
   out_3663906507468251580[71] = 0.0;
   out_3663906507468251580[72] = 0.0;
   out_3663906507468251580[73] = 0.0;
   out_3663906507468251580[74] = 0.0;
   out_3663906507468251580[75] = 0.0;
   out_3663906507468251580[76] = 1.0;
   out_3663906507468251580[77] = 0.0;
   out_3663906507468251580[78] = 0.0;
   out_3663906507468251580[79] = 0.0;
   out_3663906507468251580[80] = 0.0;
   out_3663906507468251580[81] = 0.0;
   out_3663906507468251580[82] = 0.0;
   out_3663906507468251580[83] = 0.0;
   out_3663906507468251580[84] = 0.0;
   out_3663906507468251580[85] = 0.0;
   out_3663906507468251580[86] = 0.0;
   out_3663906507468251580[87] = 0.0;
   out_3663906507468251580[88] = 0.0;
   out_3663906507468251580[89] = 0.0;
   out_3663906507468251580[90] = 0.0;
   out_3663906507468251580[91] = 0.0;
   out_3663906507468251580[92] = 0.0;
   out_3663906507468251580[93] = 0.0;
   out_3663906507468251580[94] = 0.0;
   out_3663906507468251580[95] = 1.0;
   out_3663906507468251580[96] = 0.0;
   out_3663906507468251580[97] = 0.0;
   out_3663906507468251580[98] = 0.0;
   out_3663906507468251580[99] = 0.0;
   out_3663906507468251580[100] = 0.0;
   out_3663906507468251580[101] = 0.0;
   out_3663906507468251580[102] = 0.0;
   out_3663906507468251580[103] = 0.0;
   out_3663906507468251580[104] = 0.0;
   out_3663906507468251580[105] = 0.0;
   out_3663906507468251580[106] = 0.0;
   out_3663906507468251580[107] = 0.0;
   out_3663906507468251580[108] = 0.0;
   out_3663906507468251580[109] = 0.0;
   out_3663906507468251580[110] = 0.0;
   out_3663906507468251580[111] = 0.0;
   out_3663906507468251580[112] = 0.0;
   out_3663906507468251580[113] = 0.0;
   out_3663906507468251580[114] = 1.0;
   out_3663906507468251580[115] = 0.0;
   out_3663906507468251580[116] = 0.0;
   out_3663906507468251580[117] = 0.0;
   out_3663906507468251580[118] = 0.0;
   out_3663906507468251580[119] = 0.0;
   out_3663906507468251580[120] = 0.0;
   out_3663906507468251580[121] = 0.0;
   out_3663906507468251580[122] = 0.0;
   out_3663906507468251580[123] = 0.0;
   out_3663906507468251580[124] = 0.0;
   out_3663906507468251580[125] = 0.0;
   out_3663906507468251580[126] = 0.0;
   out_3663906507468251580[127] = 0.0;
   out_3663906507468251580[128] = 0.0;
   out_3663906507468251580[129] = 0.0;
   out_3663906507468251580[130] = 0.0;
   out_3663906507468251580[131] = 0.0;
   out_3663906507468251580[132] = 0.0;
   out_3663906507468251580[133] = 1.0;
   out_3663906507468251580[134] = 0.0;
   out_3663906507468251580[135] = 0.0;
   out_3663906507468251580[136] = 0.0;
   out_3663906507468251580[137] = 0.0;
   out_3663906507468251580[138] = 0.0;
   out_3663906507468251580[139] = 0.0;
   out_3663906507468251580[140] = 0.0;
   out_3663906507468251580[141] = 0.0;
   out_3663906507468251580[142] = 0.0;
   out_3663906507468251580[143] = 0.0;
   out_3663906507468251580[144] = 0.0;
   out_3663906507468251580[145] = 0.0;
   out_3663906507468251580[146] = 0.0;
   out_3663906507468251580[147] = 0.0;
   out_3663906507468251580[148] = 0.0;
   out_3663906507468251580[149] = 0.0;
   out_3663906507468251580[150] = 0.0;
   out_3663906507468251580[151] = 0.0;
   out_3663906507468251580[152] = 1.0;
   out_3663906507468251580[153] = 0.0;
   out_3663906507468251580[154] = 0.0;
   out_3663906507468251580[155] = 0.0;
   out_3663906507468251580[156] = 0.0;
   out_3663906507468251580[157] = 0.0;
   out_3663906507468251580[158] = 0.0;
   out_3663906507468251580[159] = 0.0;
   out_3663906507468251580[160] = 0.0;
   out_3663906507468251580[161] = 0.0;
   out_3663906507468251580[162] = 0.0;
   out_3663906507468251580[163] = 0.0;
   out_3663906507468251580[164] = 0.0;
   out_3663906507468251580[165] = 0.0;
   out_3663906507468251580[166] = 0.0;
   out_3663906507468251580[167] = 0.0;
   out_3663906507468251580[168] = 0.0;
   out_3663906507468251580[169] = 0.0;
   out_3663906507468251580[170] = 0.0;
   out_3663906507468251580[171] = 1.0;
   out_3663906507468251580[172] = 0.0;
   out_3663906507468251580[173] = 0.0;
   out_3663906507468251580[174] = 0.0;
   out_3663906507468251580[175] = 0.0;
   out_3663906507468251580[176] = 0.0;
   out_3663906507468251580[177] = 0.0;
   out_3663906507468251580[178] = 0.0;
   out_3663906507468251580[179] = 0.0;
   out_3663906507468251580[180] = 0.0;
   out_3663906507468251580[181] = 0.0;
   out_3663906507468251580[182] = 0.0;
   out_3663906507468251580[183] = 0.0;
   out_3663906507468251580[184] = 0.0;
   out_3663906507468251580[185] = 0.0;
   out_3663906507468251580[186] = 0.0;
   out_3663906507468251580[187] = 0.0;
   out_3663906507468251580[188] = 0.0;
   out_3663906507468251580[189] = 0.0;
   out_3663906507468251580[190] = 1.0;
   out_3663906507468251580[191] = 0.0;
   out_3663906507468251580[192] = 0.0;
   out_3663906507468251580[193] = 0.0;
   out_3663906507468251580[194] = 0.0;
   out_3663906507468251580[195] = 0.0;
   out_3663906507468251580[196] = 0.0;
   out_3663906507468251580[197] = 0.0;
   out_3663906507468251580[198] = 0.0;
   out_3663906507468251580[199] = 0.0;
   out_3663906507468251580[200] = 0.0;
   out_3663906507468251580[201] = 0.0;
   out_3663906507468251580[202] = 0.0;
   out_3663906507468251580[203] = 0.0;
   out_3663906507468251580[204] = 0.0;
   out_3663906507468251580[205] = 0.0;
   out_3663906507468251580[206] = 0.0;
   out_3663906507468251580[207] = 0.0;
   out_3663906507468251580[208] = 0.0;
   out_3663906507468251580[209] = 1.0;
   out_3663906507468251580[210] = 0.0;
   out_3663906507468251580[211] = 0.0;
   out_3663906507468251580[212] = 0.0;
   out_3663906507468251580[213] = 0.0;
   out_3663906507468251580[214] = 0.0;
   out_3663906507468251580[215] = 0.0;
   out_3663906507468251580[216] = 0.0;
   out_3663906507468251580[217] = 0.0;
   out_3663906507468251580[218] = 0.0;
   out_3663906507468251580[219] = 0.0;
   out_3663906507468251580[220] = 0.0;
   out_3663906507468251580[221] = 0.0;
   out_3663906507468251580[222] = 0.0;
   out_3663906507468251580[223] = 0.0;
   out_3663906507468251580[224] = 0.0;
   out_3663906507468251580[225] = 0.0;
   out_3663906507468251580[226] = 0.0;
   out_3663906507468251580[227] = 0.0;
   out_3663906507468251580[228] = 1.0;
   out_3663906507468251580[229] = 0.0;
   out_3663906507468251580[230] = 0.0;
   out_3663906507468251580[231] = 0.0;
   out_3663906507468251580[232] = 0.0;
   out_3663906507468251580[233] = 0.0;
   out_3663906507468251580[234] = 0.0;
   out_3663906507468251580[235] = 0.0;
   out_3663906507468251580[236] = 0.0;
   out_3663906507468251580[237] = 0.0;
   out_3663906507468251580[238] = 0.0;
   out_3663906507468251580[239] = 0.0;
   out_3663906507468251580[240] = 0.0;
   out_3663906507468251580[241] = 0.0;
   out_3663906507468251580[242] = 0.0;
   out_3663906507468251580[243] = 0.0;
   out_3663906507468251580[244] = 0.0;
   out_3663906507468251580[245] = 0.0;
   out_3663906507468251580[246] = 0.0;
   out_3663906507468251580[247] = 1.0;
   out_3663906507468251580[248] = 0.0;
   out_3663906507468251580[249] = 0.0;
   out_3663906507468251580[250] = 0.0;
   out_3663906507468251580[251] = 0.0;
   out_3663906507468251580[252] = 0.0;
   out_3663906507468251580[253] = 0.0;
   out_3663906507468251580[254] = 0.0;
   out_3663906507468251580[255] = 0.0;
   out_3663906507468251580[256] = 0.0;
   out_3663906507468251580[257] = 0.0;
   out_3663906507468251580[258] = 0.0;
   out_3663906507468251580[259] = 0.0;
   out_3663906507468251580[260] = 0.0;
   out_3663906507468251580[261] = 0.0;
   out_3663906507468251580[262] = 0.0;
   out_3663906507468251580[263] = 0.0;
   out_3663906507468251580[264] = 0.0;
   out_3663906507468251580[265] = 0.0;
   out_3663906507468251580[266] = 1.0;
   out_3663906507468251580[267] = 0.0;
   out_3663906507468251580[268] = 0.0;
   out_3663906507468251580[269] = 0.0;
   out_3663906507468251580[270] = 0.0;
   out_3663906507468251580[271] = 0.0;
   out_3663906507468251580[272] = 0.0;
   out_3663906507468251580[273] = 0.0;
   out_3663906507468251580[274] = 0.0;
   out_3663906507468251580[275] = 0.0;
   out_3663906507468251580[276] = 0.0;
   out_3663906507468251580[277] = 0.0;
   out_3663906507468251580[278] = 0.0;
   out_3663906507468251580[279] = 0.0;
   out_3663906507468251580[280] = 0.0;
   out_3663906507468251580[281] = 0.0;
   out_3663906507468251580[282] = 0.0;
   out_3663906507468251580[283] = 0.0;
   out_3663906507468251580[284] = 0.0;
   out_3663906507468251580[285] = 1.0;
   out_3663906507468251580[286] = 0.0;
   out_3663906507468251580[287] = 0.0;
   out_3663906507468251580[288] = 0.0;
   out_3663906507468251580[289] = 0.0;
   out_3663906507468251580[290] = 0.0;
   out_3663906507468251580[291] = 0.0;
   out_3663906507468251580[292] = 0.0;
   out_3663906507468251580[293] = 0.0;
   out_3663906507468251580[294] = 0.0;
   out_3663906507468251580[295] = 0.0;
   out_3663906507468251580[296] = 0.0;
   out_3663906507468251580[297] = 0.0;
   out_3663906507468251580[298] = 0.0;
   out_3663906507468251580[299] = 0.0;
   out_3663906507468251580[300] = 0.0;
   out_3663906507468251580[301] = 0.0;
   out_3663906507468251580[302] = 0.0;
   out_3663906507468251580[303] = 0.0;
   out_3663906507468251580[304] = 1.0;
   out_3663906507468251580[305] = 0.0;
   out_3663906507468251580[306] = 0.0;
   out_3663906507468251580[307] = 0.0;
   out_3663906507468251580[308] = 0.0;
   out_3663906507468251580[309] = 0.0;
   out_3663906507468251580[310] = 0.0;
   out_3663906507468251580[311] = 0.0;
   out_3663906507468251580[312] = 0.0;
   out_3663906507468251580[313] = 0.0;
   out_3663906507468251580[314] = 0.0;
   out_3663906507468251580[315] = 0.0;
   out_3663906507468251580[316] = 0.0;
   out_3663906507468251580[317] = 0.0;
   out_3663906507468251580[318] = 0.0;
   out_3663906507468251580[319] = 0.0;
   out_3663906507468251580[320] = 0.0;
   out_3663906507468251580[321] = 0.0;
   out_3663906507468251580[322] = 0.0;
   out_3663906507468251580[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4774185451746620342) {
   out_4774185451746620342[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4774185451746620342[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4774185451746620342[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4774185451746620342[3] = dt*state[12] + state[3];
   out_4774185451746620342[4] = dt*state[13] + state[4];
   out_4774185451746620342[5] = dt*state[14] + state[5];
   out_4774185451746620342[6] = state[6];
   out_4774185451746620342[7] = state[7];
   out_4774185451746620342[8] = state[8];
   out_4774185451746620342[9] = state[9];
   out_4774185451746620342[10] = state[10];
   out_4774185451746620342[11] = state[11];
   out_4774185451746620342[12] = state[12];
   out_4774185451746620342[13] = state[13];
   out_4774185451746620342[14] = state[14];
   out_4774185451746620342[15] = state[15];
   out_4774185451746620342[16] = state[16];
   out_4774185451746620342[17] = state[17];
}
void F_fun(double *state, double dt, double *out_5859736115803136918) {
   out_5859736115803136918[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5859736115803136918[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5859736115803136918[2] = 0;
   out_5859736115803136918[3] = 0;
   out_5859736115803136918[4] = 0;
   out_5859736115803136918[5] = 0;
   out_5859736115803136918[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5859736115803136918[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5859736115803136918[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5859736115803136918[9] = 0;
   out_5859736115803136918[10] = 0;
   out_5859736115803136918[11] = 0;
   out_5859736115803136918[12] = 0;
   out_5859736115803136918[13] = 0;
   out_5859736115803136918[14] = 0;
   out_5859736115803136918[15] = 0;
   out_5859736115803136918[16] = 0;
   out_5859736115803136918[17] = 0;
   out_5859736115803136918[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5859736115803136918[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5859736115803136918[20] = 0;
   out_5859736115803136918[21] = 0;
   out_5859736115803136918[22] = 0;
   out_5859736115803136918[23] = 0;
   out_5859736115803136918[24] = 0;
   out_5859736115803136918[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5859736115803136918[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5859736115803136918[27] = 0;
   out_5859736115803136918[28] = 0;
   out_5859736115803136918[29] = 0;
   out_5859736115803136918[30] = 0;
   out_5859736115803136918[31] = 0;
   out_5859736115803136918[32] = 0;
   out_5859736115803136918[33] = 0;
   out_5859736115803136918[34] = 0;
   out_5859736115803136918[35] = 0;
   out_5859736115803136918[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5859736115803136918[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5859736115803136918[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5859736115803136918[39] = 0;
   out_5859736115803136918[40] = 0;
   out_5859736115803136918[41] = 0;
   out_5859736115803136918[42] = 0;
   out_5859736115803136918[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5859736115803136918[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5859736115803136918[45] = 0;
   out_5859736115803136918[46] = 0;
   out_5859736115803136918[47] = 0;
   out_5859736115803136918[48] = 0;
   out_5859736115803136918[49] = 0;
   out_5859736115803136918[50] = 0;
   out_5859736115803136918[51] = 0;
   out_5859736115803136918[52] = 0;
   out_5859736115803136918[53] = 0;
   out_5859736115803136918[54] = 0;
   out_5859736115803136918[55] = 0;
   out_5859736115803136918[56] = 0;
   out_5859736115803136918[57] = 1;
   out_5859736115803136918[58] = 0;
   out_5859736115803136918[59] = 0;
   out_5859736115803136918[60] = 0;
   out_5859736115803136918[61] = 0;
   out_5859736115803136918[62] = 0;
   out_5859736115803136918[63] = 0;
   out_5859736115803136918[64] = 0;
   out_5859736115803136918[65] = 0;
   out_5859736115803136918[66] = dt;
   out_5859736115803136918[67] = 0;
   out_5859736115803136918[68] = 0;
   out_5859736115803136918[69] = 0;
   out_5859736115803136918[70] = 0;
   out_5859736115803136918[71] = 0;
   out_5859736115803136918[72] = 0;
   out_5859736115803136918[73] = 0;
   out_5859736115803136918[74] = 0;
   out_5859736115803136918[75] = 0;
   out_5859736115803136918[76] = 1;
   out_5859736115803136918[77] = 0;
   out_5859736115803136918[78] = 0;
   out_5859736115803136918[79] = 0;
   out_5859736115803136918[80] = 0;
   out_5859736115803136918[81] = 0;
   out_5859736115803136918[82] = 0;
   out_5859736115803136918[83] = 0;
   out_5859736115803136918[84] = 0;
   out_5859736115803136918[85] = dt;
   out_5859736115803136918[86] = 0;
   out_5859736115803136918[87] = 0;
   out_5859736115803136918[88] = 0;
   out_5859736115803136918[89] = 0;
   out_5859736115803136918[90] = 0;
   out_5859736115803136918[91] = 0;
   out_5859736115803136918[92] = 0;
   out_5859736115803136918[93] = 0;
   out_5859736115803136918[94] = 0;
   out_5859736115803136918[95] = 1;
   out_5859736115803136918[96] = 0;
   out_5859736115803136918[97] = 0;
   out_5859736115803136918[98] = 0;
   out_5859736115803136918[99] = 0;
   out_5859736115803136918[100] = 0;
   out_5859736115803136918[101] = 0;
   out_5859736115803136918[102] = 0;
   out_5859736115803136918[103] = 0;
   out_5859736115803136918[104] = dt;
   out_5859736115803136918[105] = 0;
   out_5859736115803136918[106] = 0;
   out_5859736115803136918[107] = 0;
   out_5859736115803136918[108] = 0;
   out_5859736115803136918[109] = 0;
   out_5859736115803136918[110] = 0;
   out_5859736115803136918[111] = 0;
   out_5859736115803136918[112] = 0;
   out_5859736115803136918[113] = 0;
   out_5859736115803136918[114] = 1;
   out_5859736115803136918[115] = 0;
   out_5859736115803136918[116] = 0;
   out_5859736115803136918[117] = 0;
   out_5859736115803136918[118] = 0;
   out_5859736115803136918[119] = 0;
   out_5859736115803136918[120] = 0;
   out_5859736115803136918[121] = 0;
   out_5859736115803136918[122] = 0;
   out_5859736115803136918[123] = 0;
   out_5859736115803136918[124] = 0;
   out_5859736115803136918[125] = 0;
   out_5859736115803136918[126] = 0;
   out_5859736115803136918[127] = 0;
   out_5859736115803136918[128] = 0;
   out_5859736115803136918[129] = 0;
   out_5859736115803136918[130] = 0;
   out_5859736115803136918[131] = 0;
   out_5859736115803136918[132] = 0;
   out_5859736115803136918[133] = 1;
   out_5859736115803136918[134] = 0;
   out_5859736115803136918[135] = 0;
   out_5859736115803136918[136] = 0;
   out_5859736115803136918[137] = 0;
   out_5859736115803136918[138] = 0;
   out_5859736115803136918[139] = 0;
   out_5859736115803136918[140] = 0;
   out_5859736115803136918[141] = 0;
   out_5859736115803136918[142] = 0;
   out_5859736115803136918[143] = 0;
   out_5859736115803136918[144] = 0;
   out_5859736115803136918[145] = 0;
   out_5859736115803136918[146] = 0;
   out_5859736115803136918[147] = 0;
   out_5859736115803136918[148] = 0;
   out_5859736115803136918[149] = 0;
   out_5859736115803136918[150] = 0;
   out_5859736115803136918[151] = 0;
   out_5859736115803136918[152] = 1;
   out_5859736115803136918[153] = 0;
   out_5859736115803136918[154] = 0;
   out_5859736115803136918[155] = 0;
   out_5859736115803136918[156] = 0;
   out_5859736115803136918[157] = 0;
   out_5859736115803136918[158] = 0;
   out_5859736115803136918[159] = 0;
   out_5859736115803136918[160] = 0;
   out_5859736115803136918[161] = 0;
   out_5859736115803136918[162] = 0;
   out_5859736115803136918[163] = 0;
   out_5859736115803136918[164] = 0;
   out_5859736115803136918[165] = 0;
   out_5859736115803136918[166] = 0;
   out_5859736115803136918[167] = 0;
   out_5859736115803136918[168] = 0;
   out_5859736115803136918[169] = 0;
   out_5859736115803136918[170] = 0;
   out_5859736115803136918[171] = 1;
   out_5859736115803136918[172] = 0;
   out_5859736115803136918[173] = 0;
   out_5859736115803136918[174] = 0;
   out_5859736115803136918[175] = 0;
   out_5859736115803136918[176] = 0;
   out_5859736115803136918[177] = 0;
   out_5859736115803136918[178] = 0;
   out_5859736115803136918[179] = 0;
   out_5859736115803136918[180] = 0;
   out_5859736115803136918[181] = 0;
   out_5859736115803136918[182] = 0;
   out_5859736115803136918[183] = 0;
   out_5859736115803136918[184] = 0;
   out_5859736115803136918[185] = 0;
   out_5859736115803136918[186] = 0;
   out_5859736115803136918[187] = 0;
   out_5859736115803136918[188] = 0;
   out_5859736115803136918[189] = 0;
   out_5859736115803136918[190] = 1;
   out_5859736115803136918[191] = 0;
   out_5859736115803136918[192] = 0;
   out_5859736115803136918[193] = 0;
   out_5859736115803136918[194] = 0;
   out_5859736115803136918[195] = 0;
   out_5859736115803136918[196] = 0;
   out_5859736115803136918[197] = 0;
   out_5859736115803136918[198] = 0;
   out_5859736115803136918[199] = 0;
   out_5859736115803136918[200] = 0;
   out_5859736115803136918[201] = 0;
   out_5859736115803136918[202] = 0;
   out_5859736115803136918[203] = 0;
   out_5859736115803136918[204] = 0;
   out_5859736115803136918[205] = 0;
   out_5859736115803136918[206] = 0;
   out_5859736115803136918[207] = 0;
   out_5859736115803136918[208] = 0;
   out_5859736115803136918[209] = 1;
   out_5859736115803136918[210] = 0;
   out_5859736115803136918[211] = 0;
   out_5859736115803136918[212] = 0;
   out_5859736115803136918[213] = 0;
   out_5859736115803136918[214] = 0;
   out_5859736115803136918[215] = 0;
   out_5859736115803136918[216] = 0;
   out_5859736115803136918[217] = 0;
   out_5859736115803136918[218] = 0;
   out_5859736115803136918[219] = 0;
   out_5859736115803136918[220] = 0;
   out_5859736115803136918[221] = 0;
   out_5859736115803136918[222] = 0;
   out_5859736115803136918[223] = 0;
   out_5859736115803136918[224] = 0;
   out_5859736115803136918[225] = 0;
   out_5859736115803136918[226] = 0;
   out_5859736115803136918[227] = 0;
   out_5859736115803136918[228] = 1;
   out_5859736115803136918[229] = 0;
   out_5859736115803136918[230] = 0;
   out_5859736115803136918[231] = 0;
   out_5859736115803136918[232] = 0;
   out_5859736115803136918[233] = 0;
   out_5859736115803136918[234] = 0;
   out_5859736115803136918[235] = 0;
   out_5859736115803136918[236] = 0;
   out_5859736115803136918[237] = 0;
   out_5859736115803136918[238] = 0;
   out_5859736115803136918[239] = 0;
   out_5859736115803136918[240] = 0;
   out_5859736115803136918[241] = 0;
   out_5859736115803136918[242] = 0;
   out_5859736115803136918[243] = 0;
   out_5859736115803136918[244] = 0;
   out_5859736115803136918[245] = 0;
   out_5859736115803136918[246] = 0;
   out_5859736115803136918[247] = 1;
   out_5859736115803136918[248] = 0;
   out_5859736115803136918[249] = 0;
   out_5859736115803136918[250] = 0;
   out_5859736115803136918[251] = 0;
   out_5859736115803136918[252] = 0;
   out_5859736115803136918[253] = 0;
   out_5859736115803136918[254] = 0;
   out_5859736115803136918[255] = 0;
   out_5859736115803136918[256] = 0;
   out_5859736115803136918[257] = 0;
   out_5859736115803136918[258] = 0;
   out_5859736115803136918[259] = 0;
   out_5859736115803136918[260] = 0;
   out_5859736115803136918[261] = 0;
   out_5859736115803136918[262] = 0;
   out_5859736115803136918[263] = 0;
   out_5859736115803136918[264] = 0;
   out_5859736115803136918[265] = 0;
   out_5859736115803136918[266] = 1;
   out_5859736115803136918[267] = 0;
   out_5859736115803136918[268] = 0;
   out_5859736115803136918[269] = 0;
   out_5859736115803136918[270] = 0;
   out_5859736115803136918[271] = 0;
   out_5859736115803136918[272] = 0;
   out_5859736115803136918[273] = 0;
   out_5859736115803136918[274] = 0;
   out_5859736115803136918[275] = 0;
   out_5859736115803136918[276] = 0;
   out_5859736115803136918[277] = 0;
   out_5859736115803136918[278] = 0;
   out_5859736115803136918[279] = 0;
   out_5859736115803136918[280] = 0;
   out_5859736115803136918[281] = 0;
   out_5859736115803136918[282] = 0;
   out_5859736115803136918[283] = 0;
   out_5859736115803136918[284] = 0;
   out_5859736115803136918[285] = 1;
   out_5859736115803136918[286] = 0;
   out_5859736115803136918[287] = 0;
   out_5859736115803136918[288] = 0;
   out_5859736115803136918[289] = 0;
   out_5859736115803136918[290] = 0;
   out_5859736115803136918[291] = 0;
   out_5859736115803136918[292] = 0;
   out_5859736115803136918[293] = 0;
   out_5859736115803136918[294] = 0;
   out_5859736115803136918[295] = 0;
   out_5859736115803136918[296] = 0;
   out_5859736115803136918[297] = 0;
   out_5859736115803136918[298] = 0;
   out_5859736115803136918[299] = 0;
   out_5859736115803136918[300] = 0;
   out_5859736115803136918[301] = 0;
   out_5859736115803136918[302] = 0;
   out_5859736115803136918[303] = 0;
   out_5859736115803136918[304] = 1;
   out_5859736115803136918[305] = 0;
   out_5859736115803136918[306] = 0;
   out_5859736115803136918[307] = 0;
   out_5859736115803136918[308] = 0;
   out_5859736115803136918[309] = 0;
   out_5859736115803136918[310] = 0;
   out_5859736115803136918[311] = 0;
   out_5859736115803136918[312] = 0;
   out_5859736115803136918[313] = 0;
   out_5859736115803136918[314] = 0;
   out_5859736115803136918[315] = 0;
   out_5859736115803136918[316] = 0;
   out_5859736115803136918[317] = 0;
   out_5859736115803136918[318] = 0;
   out_5859736115803136918[319] = 0;
   out_5859736115803136918[320] = 0;
   out_5859736115803136918[321] = 0;
   out_5859736115803136918[322] = 0;
   out_5859736115803136918[323] = 1;
}
void h_4(double *state, double *unused, double *out_4561285742833549430) {
   out_4561285742833549430[0] = state[6] + state[9];
   out_4561285742833549430[1] = state[7] + state[10];
   out_4561285742833549430[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_389684428677302327) {
   out_389684428677302327[0] = 0;
   out_389684428677302327[1] = 0;
   out_389684428677302327[2] = 0;
   out_389684428677302327[3] = 0;
   out_389684428677302327[4] = 0;
   out_389684428677302327[5] = 0;
   out_389684428677302327[6] = 1;
   out_389684428677302327[7] = 0;
   out_389684428677302327[8] = 0;
   out_389684428677302327[9] = 1;
   out_389684428677302327[10] = 0;
   out_389684428677302327[11] = 0;
   out_389684428677302327[12] = 0;
   out_389684428677302327[13] = 0;
   out_389684428677302327[14] = 0;
   out_389684428677302327[15] = 0;
   out_389684428677302327[16] = 0;
   out_389684428677302327[17] = 0;
   out_389684428677302327[18] = 0;
   out_389684428677302327[19] = 0;
   out_389684428677302327[20] = 0;
   out_389684428677302327[21] = 0;
   out_389684428677302327[22] = 0;
   out_389684428677302327[23] = 0;
   out_389684428677302327[24] = 0;
   out_389684428677302327[25] = 1;
   out_389684428677302327[26] = 0;
   out_389684428677302327[27] = 0;
   out_389684428677302327[28] = 1;
   out_389684428677302327[29] = 0;
   out_389684428677302327[30] = 0;
   out_389684428677302327[31] = 0;
   out_389684428677302327[32] = 0;
   out_389684428677302327[33] = 0;
   out_389684428677302327[34] = 0;
   out_389684428677302327[35] = 0;
   out_389684428677302327[36] = 0;
   out_389684428677302327[37] = 0;
   out_389684428677302327[38] = 0;
   out_389684428677302327[39] = 0;
   out_389684428677302327[40] = 0;
   out_389684428677302327[41] = 0;
   out_389684428677302327[42] = 0;
   out_389684428677302327[43] = 0;
   out_389684428677302327[44] = 1;
   out_389684428677302327[45] = 0;
   out_389684428677302327[46] = 0;
   out_389684428677302327[47] = 1;
   out_389684428677302327[48] = 0;
   out_389684428677302327[49] = 0;
   out_389684428677302327[50] = 0;
   out_389684428677302327[51] = 0;
   out_389684428677302327[52] = 0;
   out_389684428677302327[53] = 0;
}
void h_10(double *state, double *unused, double *out_2497391090579338133) {
   out_2497391090579338133[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_2497391090579338133[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_2497391090579338133[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_1020416197739407059) {
   out_1020416197739407059[0] = 0;
   out_1020416197739407059[1] = 9.8100000000000005*cos(state[1]);
   out_1020416197739407059[2] = 0;
   out_1020416197739407059[3] = 0;
   out_1020416197739407059[4] = -state[8];
   out_1020416197739407059[5] = state[7];
   out_1020416197739407059[6] = 0;
   out_1020416197739407059[7] = state[5];
   out_1020416197739407059[8] = -state[4];
   out_1020416197739407059[9] = 0;
   out_1020416197739407059[10] = 0;
   out_1020416197739407059[11] = 0;
   out_1020416197739407059[12] = 1;
   out_1020416197739407059[13] = 0;
   out_1020416197739407059[14] = 0;
   out_1020416197739407059[15] = 1;
   out_1020416197739407059[16] = 0;
   out_1020416197739407059[17] = 0;
   out_1020416197739407059[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_1020416197739407059[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_1020416197739407059[20] = 0;
   out_1020416197739407059[21] = state[8];
   out_1020416197739407059[22] = 0;
   out_1020416197739407059[23] = -state[6];
   out_1020416197739407059[24] = -state[5];
   out_1020416197739407059[25] = 0;
   out_1020416197739407059[26] = state[3];
   out_1020416197739407059[27] = 0;
   out_1020416197739407059[28] = 0;
   out_1020416197739407059[29] = 0;
   out_1020416197739407059[30] = 0;
   out_1020416197739407059[31] = 1;
   out_1020416197739407059[32] = 0;
   out_1020416197739407059[33] = 0;
   out_1020416197739407059[34] = 1;
   out_1020416197739407059[35] = 0;
   out_1020416197739407059[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_1020416197739407059[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_1020416197739407059[38] = 0;
   out_1020416197739407059[39] = -state[7];
   out_1020416197739407059[40] = state[6];
   out_1020416197739407059[41] = 0;
   out_1020416197739407059[42] = state[4];
   out_1020416197739407059[43] = -state[3];
   out_1020416197739407059[44] = 0;
   out_1020416197739407059[45] = 0;
   out_1020416197739407059[46] = 0;
   out_1020416197739407059[47] = 0;
   out_1020416197739407059[48] = 0;
   out_1020416197739407059[49] = 0;
   out_1020416197739407059[50] = 1;
   out_1020416197739407059[51] = 0;
   out_1020416197739407059[52] = 0;
   out_1020416197739407059[53] = 1;
}
void h_13(double *state, double *unused, double *out_1021891902817546794) {
   out_1021891902817546794[0] = state[3];
   out_1021891902817546794[1] = state[4];
   out_1021891902817546794[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8000315636994003256) {
   out_8000315636994003256[0] = 0;
   out_8000315636994003256[1] = 0;
   out_8000315636994003256[2] = 0;
   out_8000315636994003256[3] = 1;
   out_8000315636994003256[4] = 0;
   out_8000315636994003256[5] = 0;
   out_8000315636994003256[6] = 0;
   out_8000315636994003256[7] = 0;
   out_8000315636994003256[8] = 0;
   out_8000315636994003256[9] = 0;
   out_8000315636994003256[10] = 0;
   out_8000315636994003256[11] = 0;
   out_8000315636994003256[12] = 0;
   out_8000315636994003256[13] = 0;
   out_8000315636994003256[14] = 0;
   out_8000315636994003256[15] = 0;
   out_8000315636994003256[16] = 0;
   out_8000315636994003256[17] = 0;
   out_8000315636994003256[18] = 0;
   out_8000315636994003256[19] = 0;
   out_8000315636994003256[20] = 0;
   out_8000315636994003256[21] = 0;
   out_8000315636994003256[22] = 1;
   out_8000315636994003256[23] = 0;
   out_8000315636994003256[24] = 0;
   out_8000315636994003256[25] = 0;
   out_8000315636994003256[26] = 0;
   out_8000315636994003256[27] = 0;
   out_8000315636994003256[28] = 0;
   out_8000315636994003256[29] = 0;
   out_8000315636994003256[30] = 0;
   out_8000315636994003256[31] = 0;
   out_8000315636994003256[32] = 0;
   out_8000315636994003256[33] = 0;
   out_8000315636994003256[34] = 0;
   out_8000315636994003256[35] = 0;
   out_8000315636994003256[36] = 0;
   out_8000315636994003256[37] = 0;
   out_8000315636994003256[38] = 0;
   out_8000315636994003256[39] = 0;
   out_8000315636994003256[40] = 0;
   out_8000315636994003256[41] = 1;
   out_8000315636994003256[42] = 0;
   out_8000315636994003256[43] = 0;
   out_8000315636994003256[44] = 0;
   out_8000315636994003256[45] = 0;
   out_8000315636994003256[46] = 0;
   out_8000315636994003256[47] = 0;
   out_8000315636994003256[48] = 0;
   out_8000315636994003256[49] = 0;
   out_8000315636994003256[50] = 0;
   out_8000315636994003256[51] = 0;
   out_8000315636994003256[52] = 0;
   out_8000315636994003256[53] = 0;
}
void h_14(double *state, double *unused, double *out_3304628372857441851) {
   out_3304628372857441851[0] = state[6];
   out_3304628372857441851[1] = state[7];
   out_3304628372857441851[2] = state[8];
}
void H_14(double *state, double *unused, double *out_4352925285016786856) {
   out_4352925285016786856[0] = 0;
   out_4352925285016786856[1] = 0;
   out_4352925285016786856[2] = 0;
   out_4352925285016786856[3] = 0;
   out_4352925285016786856[4] = 0;
   out_4352925285016786856[5] = 0;
   out_4352925285016786856[6] = 1;
   out_4352925285016786856[7] = 0;
   out_4352925285016786856[8] = 0;
   out_4352925285016786856[9] = 0;
   out_4352925285016786856[10] = 0;
   out_4352925285016786856[11] = 0;
   out_4352925285016786856[12] = 0;
   out_4352925285016786856[13] = 0;
   out_4352925285016786856[14] = 0;
   out_4352925285016786856[15] = 0;
   out_4352925285016786856[16] = 0;
   out_4352925285016786856[17] = 0;
   out_4352925285016786856[18] = 0;
   out_4352925285016786856[19] = 0;
   out_4352925285016786856[20] = 0;
   out_4352925285016786856[21] = 0;
   out_4352925285016786856[22] = 0;
   out_4352925285016786856[23] = 0;
   out_4352925285016786856[24] = 0;
   out_4352925285016786856[25] = 1;
   out_4352925285016786856[26] = 0;
   out_4352925285016786856[27] = 0;
   out_4352925285016786856[28] = 0;
   out_4352925285016786856[29] = 0;
   out_4352925285016786856[30] = 0;
   out_4352925285016786856[31] = 0;
   out_4352925285016786856[32] = 0;
   out_4352925285016786856[33] = 0;
   out_4352925285016786856[34] = 0;
   out_4352925285016786856[35] = 0;
   out_4352925285016786856[36] = 0;
   out_4352925285016786856[37] = 0;
   out_4352925285016786856[38] = 0;
   out_4352925285016786856[39] = 0;
   out_4352925285016786856[40] = 0;
   out_4352925285016786856[41] = 0;
   out_4352925285016786856[42] = 0;
   out_4352925285016786856[43] = 0;
   out_4352925285016786856[44] = 1;
   out_4352925285016786856[45] = 0;
   out_4352925285016786856[46] = 0;
   out_4352925285016786856[47] = 0;
   out_4352925285016786856[48] = 0;
   out_4352925285016786856[49] = 0;
   out_4352925285016786856[50] = 0;
   out_4352925285016786856[51] = 0;
   out_4352925285016786856[52] = 0;
   out_4352925285016786856[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_6287899668351208780) {
  err_fun(nom_x, delta_x, out_6287899668351208780);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4433323129515526623) {
  inv_err_fun(nom_x, true_x, out_4433323129515526623);
}
void pose_H_mod_fun(double *state, double *out_3663906507468251580) {
  H_mod_fun(state, out_3663906507468251580);
}
void pose_f_fun(double *state, double dt, double *out_4774185451746620342) {
  f_fun(state,  dt, out_4774185451746620342);
}
void pose_F_fun(double *state, double dt, double *out_5859736115803136918) {
  F_fun(state,  dt, out_5859736115803136918);
}
void pose_h_4(double *state, double *unused, double *out_4561285742833549430) {
  h_4(state, unused, out_4561285742833549430);
}
void pose_H_4(double *state, double *unused, double *out_389684428677302327) {
  H_4(state, unused, out_389684428677302327);
}
void pose_h_10(double *state, double *unused, double *out_2497391090579338133) {
  h_10(state, unused, out_2497391090579338133);
}
void pose_H_10(double *state, double *unused, double *out_1020416197739407059) {
  H_10(state, unused, out_1020416197739407059);
}
void pose_h_13(double *state, double *unused, double *out_1021891902817546794) {
  h_13(state, unused, out_1021891902817546794);
}
void pose_H_13(double *state, double *unused, double *out_8000315636994003256) {
  H_13(state, unused, out_8000315636994003256);
}
void pose_h_14(double *state, double *unused, double *out_3304628372857441851) {
  h_14(state, unused, out_3304628372857441851);
}
void pose_H_14(double *state, double *unused, double *out_4352925285016786856) {
  H_14(state, unused, out_4352925285016786856);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
