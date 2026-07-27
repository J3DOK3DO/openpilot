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
void err_fun(double *nom_x, double *delta_x, double *out_2355293272416553220) {
   out_2355293272416553220[0] = delta_x[0] + nom_x[0];
   out_2355293272416553220[1] = delta_x[1] + nom_x[1];
   out_2355293272416553220[2] = delta_x[2] + nom_x[2];
   out_2355293272416553220[3] = delta_x[3] + nom_x[3];
   out_2355293272416553220[4] = delta_x[4] + nom_x[4];
   out_2355293272416553220[5] = delta_x[5] + nom_x[5];
   out_2355293272416553220[6] = delta_x[6] + nom_x[6];
   out_2355293272416553220[7] = delta_x[7] + nom_x[7];
   out_2355293272416553220[8] = delta_x[8] + nom_x[8];
   out_2355293272416553220[9] = delta_x[9] + nom_x[9];
   out_2355293272416553220[10] = delta_x[10] + nom_x[10];
   out_2355293272416553220[11] = delta_x[11] + nom_x[11];
   out_2355293272416553220[12] = delta_x[12] + nom_x[12];
   out_2355293272416553220[13] = delta_x[13] + nom_x[13];
   out_2355293272416553220[14] = delta_x[14] + nom_x[14];
   out_2355293272416553220[15] = delta_x[15] + nom_x[15];
   out_2355293272416553220[16] = delta_x[16] + nom_x[16];
   out_2355293272416553220[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_4800523972292248179) {
   out_4800523972292248179[0] = -nom_x[0] + true_x[0];
   out_4800523972292248179[1] = -nom_x[1] + true_x[1];
   out_4800523972292248179[2] = -nom_x[2] + true_x[2];
   out_4800523972292248179[3] = -nom_x[3] + true_x[3];
   out_4800523972292248179[4] = -nom_x[4] + true_x[4];
   out_4800523972292248179[5] = -nom_x[5] + true_x[5];
   out_4800523972292248179[6] = -nom_x[6] + true_x[6];
   out_4800523972292248179[7] = -nom_x[7] + true_x[7];
   out_4800523972292248179[8] = -nom_x[8] + true_x[8];
   out_4800523972292248179[9] = -nom_x[9] + true_x[9];
   out_4800523972292248179[10] = -nom_x[10] + true_x[10];
   out_4800523972292248179[11] = -nom_x[11] + true_x[11];
   out_4800523972292248179[12] = -nom_x[12] + true_x[12];
   out_4800523972292248179[13] = -nom_x[13] + true_x[13];
   out_4800523972292248179[14] = -nom_x[14] + true_x[14];
   out_4800523972292248179[15] = -nom_x[15] + true_x[15];
   out_4800523972292248179[16] = -nom_x[16] + true_x[16];
   out_4800523972292248179[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_1756056773937278960) {
   out_1756056773937278960[0] = 1.0;
   out_1756056773937278960[1] = 0.0;
   out_1756056773937278960[2] = 0.0;
   out_1756056773937278960[3] = 0.0;
   out_1756056773937278960[4] = 0.0;
   out_1756056773937278960[5] = 0.0;
   out_1756056773937278960[6] = 0.0;
   out_1756056773937278960[7] = 0.0;
   out_1756056773937278960[8] = 0.0;
   out_1756056773937278960[9] = 0.0;
   out_1756056773937278960[10] = 0.0;
   out_1756056773937278960[11] = 0.0;
   out_1756056773937278960[12] = 0.0;
   out_1756056773937278960[13] = 0.0;
   out_1756056773937278960[14] = 0.0;
   out_1756056773937278960[15] = 0.0;
   out_1756056773937278960[16] = 0.0;
   out_1756056773937278960[17] = 0.0;
   out_1756056773937278960[18] = 0.0;
   out_1756056773937278960[19] = 1.0;
   out_1756056773937278960[20] = 0.0;
   out_1756056773937278960[21] = 0.0;
   out_1756056773937278960[22] = 0.0;
   out_1756056773937278960[23] = 0.0;
   out_1756056773937278960[24] = 0.0;
   out_1756056773937278960[25] = 0.0;
   out_1756056773937278960[26] = 0.0;
   out_1756056773937278960[27] = 0.0;
   out_1756056773937278960[28] = 0.0;
   out_1756056773937278960[29] = 0.0;
   out_1756056773937278960[30] = 0.0;
   out_1756056773937278960[31] = 0.0;
   out_1756056773937278960[32] = 0.0;
   out_1756056773937278960[33] = 0.0;
   out_1756056773937278960[34] = 0.0;
   out_1756056773937278960[35] = 0.0;
   out_1756056773937278960[36] = 0.0;
   out_1756056773937278960[37] = 0.0;
   out_1756056773937278960[38] = 1.0;
   out_1756056773937278960[39] = 0.0;
   out_1756056773937278960[40] = 0.0;
   out_1756056773937278960[41] = 0.0;
   out_1756056773937278960[42] = 0.0;
   out_1756056773937278960[43] = 0.0;
   out_1756056773937278960[44] = 0.0;
   out_1756056773937278960[45] = 0.0;
   out_1756056773937278960[46] = 0.0;
   out_1756056773937278960[47] = 0.0;
   out_1756056773937278960[48] = 0.0;
   out_1756056773937278960[49] = 0.0;
   out_1756056773937278960[50] = 0.0;
   out_1756056773937278960[51] = 0.0;
   out_1756056773937278960[52] = 0.0;
   out_1756056773937278960[53] = 0.0;
   out_1756056773937278960[54] = 0.0;
   out_1756056773937278960[55] = 0.0;
   out_1756056773937278960[56] = 0.0;
   out_1756056773937278960[57] = 1.0;
   out_1756056773937278960[58] = 0.0;
   out_1756056773937278960[59] = 0.0;
   out_1756056773937278960[60] = 0.0;
   out_1756056773937278960[61] = 0.0;
   out_1756056773937278960[62] = 0.0;
   out_1756056773937278960[63] = 0.0;
   out_1756056773937278960[64] = 0.0;
   out_1756056773937278960[65] = 0.0;
   out_1756056773937278960[66] = 0.0;
   out_1756056773937278960[67] = 0.0;
   out_1756056773937278960[68] = 0.0;
   out_1756056773937278960[69] = 0.0;
   out_1756056773937278960[70] = 0.0;
   out_1756056773937278960[71] = 0.0;
   out_1756056773937278960[72] = 0.0;
   out_1756056773937278960[73] = 0.0;
   out_1756056773937278960[74] = 0.0;
   out_1756056773937278960[75] = 0.0;
   out_1756056773937278960[76] = 1.0;
   out_1756056773937278960[77] = 0.0;
   out_1756056773937278960[78] = 0.0;
   out_1756056773937278960[79] = 0.0;
   out_1756056773937278960[80] = 0.0;
   out_1756056773937278960[81] = 0.0;
   out_1756056773937278960[82] = 0.0;
   out_1756056773937278960[83] = 0.0;
   out_1756056773937278960[84] = 0.0;
   out_1756056773937278960[85] = 0.0;
   out_1756056773937278960[86] = 0.0;
   out_1756056773937278960[87] = 0.0;
   out_1756056773937278960[88] = 0.0;
   out_1756056773937278960[89] = 0.0;
   out_1756056773937278960[90] = 0.0;
   out_1756056773937278960[91] = 0.0;
   out_1756056773937278960[92] = 0.0;
   out_1756056773937278960[93] = 0.0;
   out_1756056773937278960[94] = 0.0;
   out_1756056773937278960[95] = 1.0;
   out_1756056773937278960[96] = 0.0;
   out_1756056773937278960[97] = 0.0;
   out_1756056773937278960[98] = 0.0;
   out_1756056773937278960[99] = 0.0;
   out_1756056773937278960[100] = 0.0;
   out_1756056773937278960[101] = 0.0;
   out_1756056773937278960[102] = 0.0;
   out_1756056773937278960[103] = 0.0;
   out_1756056773937278960[104] = 0.0;
   out_1756056773937278960[105] = 0.0;
   out_1756056773937278960[106] = 0.0;
   out_1756056773937278960[107] = 0.0;
   out_1756056773937278960[108] = 0.0;
   out_1756056773937278960[109] = 0.0;
   out_1756056773937278960[110] = 0.0;
   out_1756056773937278960[111] = 0.0;
   out_1756056773937278960[112] = 0.0;
   out_1756056773937278960[113] = 0.0;
   out_1756056773937278960[114] = 1.0;
   out_1756056773937278960[115] = 0.0;
   out_1756056773937278960[116] = 0.0;
   out_1756056773937278960[117] = 0.0;
   out_1756056773937278960[118] = 0.0;
   out_1756056773937278960[119] = 0.0;
   out_1756056773937278960[120] = 0.0;
   out_1756056773937278960[121] = 0.0;
   out_1756056773937278960[122] = 0.0;
   out_1756056773937278960[123] = 0.0;
   out_1756056773937278960[124] = 0.0;
   out_1756056773937278960[125] = 0.0;
   out_1756056773937278960[126] = 0.0;
   out_1756056773937278960[127] = 0.0;
   out_1756056773937278960[128] = 0.0;
   out_1756056773937278960[129] = 0.0;
   out_1756056773937278960[130] = 0.0;
   out_1756056773937278960[131] = 0.0;
   out_1756056773937278960[132] = 0.0;
   out_1756056773937278960[133] = 1.0;
   out_1756056773937278960[134] = 0.0;
   out_1756056773937278960[135] = 0.0;
   out_1756056773937278960[136] = 0.0;
   out_1756056773937278960[137] = 0.0;
   out_1756056773937278960[138] = 0.0;
   out_1756056773937278960[139] = 0.0;
   out_1756056773937278960[140] = 0.0;
   out_1756056773937278960[141] = 0.0;
   out_1756056773937278960[142] = 0.0;
   out_1756056773937278960[143] = 0.0;
   out_1756056773937278960[144] = 0.0;
   out_1756056773937278960[145] = 0.0;
   out_1756056773937278960[146] = 0.0;
   out_1756056773937278960[147] = 0.0;
   out_1756056773937278960[148] = 0.0;
   out_1756056773937278960[149] = 0.0;
   out_1756056773937278960[150] = 0.0;
   out_1756056773937278960[151] = 0.0;
   out_1756056773937278960[152] = 1.0;
   out_1756056773937278960[153] = 0.0;
   out_1756056773937278960[154] = 0.0;
   out_1756056773937278960[155] = 0.0;
   out_1756056773937278960[156] = 0.0;
   out_1756056773937278960[157] = 0.0;
   out_1756056773937278960[158] = 0.0;
   out_1756056773937278960[159] = 0.0;
   out_1756056773937278960[160] = 0.0;
   out_1756056773937278960[161] = 0.0;
   out_1756056773937278960[162] = 0.0;
   out_1756056773937278960[163] = 0.0;
   out_1756056773937278960[164] = 0.0;
   out_1756056773937278960[165] = 0.0;
   out_1756056773937278960[166] = 0.0;
   out_1756056773937278960[167] = 0.0;
   out_1756056773937278960[168] = 0.0;
   out_1756056773937278960[169] = 0.0;
   out_1756056773937278960[170] = 0.0;
   out_1756056773937278960[171] = 1.0;
   out_1756056773937278960[172] = 0.0;
   out_1756056773937278960[173] = 0.0;
   out_1756056773937278960[174] = 0.0;
   out_1756056773937278960[175] = 0.0;
   out_1756056773937278960[176] = 0.0;
   out_1756056773937278960[177] = 0.0;
   out_1756056773937278960[178] = 0.0;
   out_1756056773937278960[179] = 0.0;
   out_1756056773937278960[180] = 0.0;
   out_1756056773937278960[181] = 0.0;
   out_1756056773937278960[182] = 0.0;
   out_1756056773937278960[183] = 0.0;
   out_1756056773937278960[184] = 0.0;
   out_1756056773937278960[185] = 0.0;
   out_1756056773937278960[186] = 0.0;
   out_1756056773937278960[187] = 0.0;
   out_1756056773937278960[188] = 0.0;
   out_1756056773937278960[189] = 0.0;
   out_1756056773937278960[190] = 1.0;
   out_1756056773937278960[191] = 0.0;
   out_1756056773937278960[192] = 0.0;
   out_1756056773937278960[193] = 0.0;
   out_1756056773937278960[194] = 0.0;
   out_1756056773937278960[195] = 0.0;
   out_1756056773937278960[196] = 0.0;
   out_1756056773937278960[197] = 0.0;
   out_1756056773937278960[198] = 0.0;
   out_1756056773937278960[199] = 0.0;
   out_1756056773937278960[200] = 0.0;
   out_1756056773937278960[201] = 0.0;
   out_1756056773937278960[202] = 0.0;
   out_1756056773937278960[203] = 0.0;
   out_1756056773937278960[204] = 0.0;
   out_1756056773937278960[205] = 0.0;
   out_1756056773937278960[206] = 0.0;
   out_1756056773937278960[207] = 0.0;
   out_1756056773937278960[208] = 0.0;
   out_1756056773937278960[209] = 1.0;
   out_1756056773937278960[210] = 0.0;
   out_1756056773937278960[211] = 0.0;
   out_1756056773937278960[212] = 0.0;
   out_1756056773937278960[213] = 0.0;
   out_1756056773937278960[214] = 0.0;
   out_1756056773937278960[215] = 0.0;
   out_1756056773937278960[216] = 0.0;
   out_1756056773937278960[217] = 0.0;
   out_1756056773937278960[218] = 0.0;
   out_1756056773937278960[219] = 0.0;
   out_1756056773937278960[220] = 0.0;
   out_1756056773937278960[221] = 0.0;
   out_1756056773937278960[222] = 0.0;
   out_1756056773937278960[223] = 0.0;
   out_1756056773937278960[224] = 0.0;
   out_1756056773937278960[225] = 0.0;
   out_1756056773937278960[226] = 0.0;
   out_1756056773937278960[227] = 0.0;
   out_1756056773937278960[228] = 1.0;
   out_1756056773937278960[229] = 0.0;
   out_1756056773937278960[230] = 0.0;
   out_1756056773937278960[231] = 0.0;
   out_1756056773937278960[232] = 0.0;
   out_1756056773937278960[233] = 0.0;
   out_1756056773937278960[234] = 0.0;
   out_1756056773937278960[235] = 0.0;
   out_1756056773937278960[236] = 0.0;
   out_1756056773937278960[237] = 0.0;
   out_1756056773937278960[238] = 0.0;
   out_1756056773937278960[239] = 0.0;
   out_1756056773937278960[240] = 0.0;
   out_1756056773937278960[241] = 0.0;
   out_1756056773937278960[242] = 0.0;
   out_1756056773937278960[243] = 0.0;
   out_1756056773937278960[244] = 0.0;
   out_1756056773937278960[245] = 0.0;
   out_1756056773937278960[246] = 0.0;
   out_1756056773937278960[247] = 1.0;
   out_1756056773937278960[248] = 0.0;
   out_1756056773937278960[249] = 0.0;
   out_1756056773937278960[250] = 0.0;
   out_1756056773937278960[251] = 0.0;
   out_1756056773937278960[252] = 0.0;
   out_1756056773937278960[253] = 0.0;
   out_1756056773937278960[254] = 0.0;
   out_1756056773937278960[255] = 0.0;
   out_1756056773937278960[256] = 0.0;
   out_1756056773937278960[257] = 0.0;
   out_1756056773937278960[258] = 0.0;
   out_1756056773937278960[259] = 0.0;
   out_1756056773937278960[260] = 0.0;
   out_1756056773937278960[261] = 0.0;
   out_1756056773937278960[262] = 0.0;
   out_1756056773937278960[263] = 0.0;
   out_1756056773937278960[264] = 0.0;
   out_1756056773937278960[265] = 0.0;
   out_1756056773937278960[266] = 1.0;
   out_1756056773937278960[267] = 0.0;
   out_1756056773937278960[268] = 0.0;
   out_1756056773937278960[269] = 0.0;
   out_1756056773937278960[270] = 0.0;
   out_1756056773937278960[271] = 0.0;
   out_1756056773937278960[272] = 0.0;
   out_1756056773937278960[273] = 0.0;
   out_1756056773937278960[274] = 0.0;
   out_1756056773937278960[275] = 0.0;
   out_1756056773937278960[276] = 0.0;
   out_1756056773937278960[277] = 0.0;
   out_1756056773937278960[278] = 0.0;
   out_1756056773937278960[279] = 0.0;
   out_1756056773937278960[280] = 0.0;
   out_1756056773937278960[281] = 0.0;
   out_1756056773937278960[282] = 0.0;
   out_1756056773937278960[283] = 0.0;
   out_1756056773937278960[284] = 0.0;
   out_1756056773937278960[285] = 1.0;
   out_1756056773937278960[286] = 0.0;
   out_1756056773937278960[287] = 0.0;
   out_1756056773937278960[288] = 0.0;
   out_1756056773937278960[289] = 0.0;
   out_1756056773937278960[290] = 0.0;
   out_1756056773937278960[291] = 0.0;
   out_1756056773937278960[292] = 0.0;
   out_1756056773937278960[293] = 0.0;
   out_1756056773937278960[294] = 0.0;
   out_1756056773937278960[295] = 0.0;
   out_1756056773937278960[296] = 0.0;
   out_1756056773937278960[297] = 0.0;
   out_1756056773937278960[298] = 0.0;
   out_1756056773937278960[299] = 0.0;
   out_1756056773937278960[300] = 0.0;
   out_1756056773937278960[301] = 0.0;
   out_1756056773937278960[302] = 0.0;
   out_1756056773937278960[303] = 0.0;
   out_1756056773937278960[304] = 1.0;
   out_1756056773937278960[305] = 0.0;
   out_1756056773937278960[306] = 0.0;
   out_1756056773937278960[307] = 0.0;
   out_1756056773937278960[308] = 0.0;
   out_1756056773937278960[309] = 0.0;
   out_1756056773937278960[310] = 0.0;
   out_1756056773937278960[311] = 0.0;
   out_1756056773937278960[312] = 0.0;
   out_1756056773937278960[313] = 0.0;
   out_1756056773937278960[314] = 0.0;
   out_1756056773937278960[315] = 0.0;
   out_1756056773937278960[316] = 0.0;
   out_1756056773937278960[317] = 0.0;
   out_1756056773937278960[318] = 0.0;
   out_1756056773937278960[319] = 0.0;
   out_1756056773937278960[320] = 0.0;
   out_1756056773937278960[321] = 0.0;
   out_1756056773937278960[322] = 0.0;
   out_1756056773937278960[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4431905570801982118) {
   out_4431905570801982118[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4431905570801982118[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4431905570801982118[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4431905570801982118[3] = dt*state[12] + state[3];
   out_4431905570801982118[4] = dt*state[13] + state[4];
   out_4431905570801982118[5] = dt*state[14] + state[5];
   out_4431905570801982118[6] = state[6];
   out_4431905570801982118[7] = state[7];
   out_4431905570801982118[8] = state[8];
   out_4431905570801982118[9] = state[9];
   out_4431905570801982118[10] = state[10];
   out_4431905570801982118[11] = state[11];
   out_4431905570801982118[12] = state[12];
   out_4431905570801982118[13] = state[13];
   out_4431905570801982118[14] = state[14];
   out_4431905570801982118[15] = state[15];
   out_4431905570801982118[16] = state[16];
   out_4431905570801982118[17] = state[17];
}
void F_fun(double *state, double dt, double *out_2871178270800665939) {
   out_2871178270800665939[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2871178270800665939[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2871178270800665939[2] = 0;
   out_2871178270800665939[3] = 0;
   out_2871178270800665939[4] = 0;
   out_2871178270800665939[5] = 0;
   out_2871178270800665939[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2871178270800665939[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2871178270800665939[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2871178270800665939[9] = 0;
   out_2871178270800665939[10] = 0;
   out_2871178270800665939[11] = 0;
   out_2871178270800665939[12] = 0;
   out_2871178270800665939[13] = 0;
   out_2871178270800665939[14] = 0;
   out_2871178270800665939[15] = 0;
   out_2871178270800665939[16] = 0;
   out_2871178270800665939[17] = 0;
   out_2871178270800665939[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2871178270800665939[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2871178270800665939[20] = 0;
   out_2871178270800665939[21] = 0;
   out_2871178270800665939[22] = 0;
   out_2871178270800665939[23] = 0;
   out_2871178270800665939[24] = 0;
   out_2871178270800665939[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2871178270800665939[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2871178270800665939[27] = 0;
   out_2871178270800665939[28] = 0;
   out_2871178270800665939[29] = 0;
   out_2871178270800665939[30] = 0;
   out_2871178270800665939[31] = 0;
   out_2871178270800665939[32] = 0;
   out_2871178270800665939[33] = 0;
   out_2871178270800665939[34] = 0;
   out_2871178270800665939[35] = 0;
   out_2871178270800665939[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2871178270800665939[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2871178270800665939[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2871178270800665939[39] = 0;
   out_2871178270800665939[40] = 0;
   out_2871178270800665939[41] = 0;
   out_2871178270800665939[42] = 0;
   out_2871178270800665939[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2871178270800665939[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2871178270800665939[45] = 0;
   out_2871178270800665939[46] = 0;
   out_2871178270800665939[47] = 0;
   out_2871178270800665939[48] = 0;
   out_2871178270800665939[49] = 0;
   out_2871178270800665939[50] = 0;
   out_2871178270800665939[51] = 0;
   out_2871178270800665939[52] = 0;
   out_2871178270800665939[53] = 0;
   out_2871178270800665939[54] = 0;
   out_2871178270800665939[55] = 0;
   out_2871178270800665939[56] = 0;
   out_2871178270800665939[57] = 1;
   out_2871178270800665939[58] = 0;
   out_2871178270800665939[59] = 0;
   out_2871178270800665939[60] = 0;
   out_2871178270800665939[61] = 0;
   out_2871178270800665939[62] = 0;
   out_2871178270800665939[63] = 0;
   out_2871178270800665939[64] = 0;
   out_2871178270800665939[65] = 0;
   out_2871178270800665939[66] = dt;
   out_2871178270800665939[67] = 0;
   out_2871178270800665939[68] = 0;
   out_2871178270800665939[69] = 0;
   out_2871178270800665939[70] = 0;
   out_2871178270800665939[71] = 0;
   out_2871178270800665939[72] = 0;
   out_2871178270800665939[73] = 0;
   out_2871178270800665939[74] = 0;
   out_2871178270800665939[75] = 0;
   out_2871178270800665939[76] = 1;
   out_2871178270800665939[77] = 0;
   out_2871178270800665939[78] = 0;
   out_2871178270800665939[79] = 0;
   out_2871178270800665939[80] = 0;
   out_2871178270800665939[81] = 0;
   out_2871178270800665939[82] = 0;
   out_2871178270800665939[83] = 0;
   out_2871178270800665939[84] = 0;
   out_2871178270800665939[85] = dt;
   out_2871178270800665939[86] = 0;
   out_2871178270800665939[87] = 0;
   out_2871178270800665939[88] = 0;
   out_2871178270800665939[89] = 0;
   out_2871178270800665939[90] = 0;
   out_2871178270800665939[91] = 0;
   out_2871178270800665939[92] = 0;
   out_2871178270800665939[93] = 0;
   out_2871178270800665939[94] = 0;
   out_2871178270800665939[95] = 1;
   out_2871178270800665939[96] = 0;
   out_2871178270800665939[97] = 0;
   out_2871178270800665939[98] = 0;
   out_2871178270800665939[99] = 0;
   out_2871178270800665939[100] = 0;
   out_2871178270800665939[101] = 0;
   out_2871178270800665939[102] = 0;
   out_2871178270800665939[103] = 0;
   out_2871178270800665939[104] = dt;
   out_2871178270800665939[105] = 0;
   out_2871178270800665939[106] = 0;
   out_2871178270800665939[107] = 0;
   out_2871178270800665939[108] = 0;
   out_2871178270800665939[109] = 0;
   out_2871178270800665939[110] = 0;
   out_2871178270800665939[111] = 0;
   out_2871178270800665939[112] = 0;
   out_2871178270800665939[113] = 0;
   out_2871178270800665939[114] = 1;
   out_2871178270800665939[115] = 0;
   out_2871178270800665939[116] = 0;
   out_2871178270800665939[117] = 0;
   out_2871178270800665939[118] = 0;
   out_2871178270800665939[119] = 0;
   out_2871178270800665939[120] = 0;
   out_2871178270800665939[121] = 0;
   out_2871178270800665939[122] = 0;
   out_2871178270800665939[123] = 0;
   out_2871178270800665939[124] = 0;
   out_2871178270800665939[125] = 0;
   out_2871178270800665939[126] = 0;
   out_2871178270800665939[127] = 0;
   out_2871178270800665939[128] = 0;
   out_2871178270800665939[129] = 0;
   out_2871178270800665939[130] = 0;
   out_2871178270800665939[131] = 0;
   out_2871178270800665939[132] = 0;
   out_2871178270800665939[133] = 1;
   out_2871178270800665939[134] = 0;
   out_2871178270800665939[135] = 0;
   out_2871178270800665939[136] = 0;
   out_2871178270800665939[137] = 0;
   out_2871178270800665939[138] = 0;
   out_2871178270800665939[139] = 0;
   out_2871178270800665939[140] = 0;
   out_2871178270800665939[141] = 0;
   out_2871178270800665939[142] = 0;
   out_2871178270800665939[143] = 0;
   out_2871178270800665939[144] = 0;
   out_2871178270800665939[145] = 0;
   out_2871178270800665939[146] = 0;
   out_2871178270800665939[147] = 0;
   out_2871178270800665939[148] = 0;
   out_2871178270800665939[149] = 0;
   out_2871178270800665939[150] = 0;
   out_2871178270800665939[151] = 0;
   out_2871178270800665939[152] = 1;
   out_2871178270800665939[153] = 0;
   out_2871178270800665939[154] = 0;
   out_2871178270800665939[155] = 0;
   out_2871178270800665939[156] = 0;
   out_2871178270800665939[157] = 0;
   out_2871178270800665939[158] = 0;
   out_2871178270800665939[159] = 0;
   out_2871178270800665939[160] = 0;
   out_2871178270800665939[161] = 0;
   out_2871178270800665939[162] = 0;
   out_2871178270800665939[163] = 0;
   out_2871178270800665939[164] = 0;
   out_2871178270800665939[165] = 0;
   out_2871178270800665939[166] = 0;
   out_2871178270800665939[167] = 0;
   out_2871178270800665939[168] = 0;
   out_2871178270800665939[169] = 0;
   out_2871178270800665939[170] = 0;
   out_2871178270800665939[171] = 1;
   out_2871178270800665939[172] = 0;
   out_2871178270800665939[173] = 0;
   out_2871178270800665939[174] = 0;
   out_2871178270800665939[175] = 0;
   out_2871178270800665939[176] = 0;
   out_2871178270800665939[177] = 0;
   out_2871178270800665939[178] = 0;
   out_2871178270800665939[179] = 0;
   out_2871178270800665939[180] = 0;
   out_2871178270800665939[181] = 0;
   out_2871178270800665939[182] = 0;
   out_2871178270800665939[183] = 0;
   out_2871178270800665939[184] = 0;
   out_2871178270800665939[185] = 0;
   out_2871178270800665939[186] = 0;
   out_2871178270800665939[187] = 0;
   out_2871178270800665939[188] = 0;
   out_2871178270800665939[189] = 0;
   out_2871178270800665939[190] = 1;
   out_2871178270800665939[191] = 0;
   out_2871178270800665939[192] = 0;
   out_2871178270800665939[193] = 0;
   out_2871178270800665939[194] = 0;
   out_2871178270800665939[195] = 0;
   out_2871178270800665939[196] = 0;
   out_2871178270800665939[197] = 0;
   out_2871178270800665939[198] = 0;
   out_2871178270800665939[199] = 0;
   out_2871178270800665939[200] = 0;
   out_2871178270800665939[201] = 0;
   out_2871178270800665939[202] = 0;
   out_2871178270800665939[203] = 0;
   out_2871178270800665939[204] = 0;
   out_2871178270800665939[205] = 0;
   out_2871178270800665939[206] = 0;
   out_2871178270800665939[207] = 0;
   out_2871178270800665939[208] = 0;
   out_2871178270800665939[209] = 1;
   out_2871178270800665939[210] = 0;
   out_2871178270800665939[211] = 0;
   out_2871178270800665939[212] = 0;
   out_2871178270800665939[213] = 0;
   out_2871178270800665939[214] = 0;
   out_2871178270800665939[215] = 0;
   out_2871178270800665939[216] = 0;
   out_2871178270800665939[217] = 0;
   out_2871178270800665939[218] = 0;
   out_2871178270800665939[219] = 0;
   out_2871178270800665939[220] = 0;
   out_2871178270800665939[221] = 0;
   out_2871178270800665939[222] = 0;
   out_2871178270800665939[223] = 0;
   out_2871178270800665939[224] = 0;
   out_2871178270800665939[225] = 0;
   out_2871178270800665939[226] = 0;
   out_2871178270800665939[227] = 0;
   out_2871178270800665939[228] = 1;
   out_2871178270800665939[229] = 0;
   out_2871178270800665939[230] = 0;
   out_2871178270800665939[231] = 0;
   out_2871178270800665939[232] = 0;
   out_2871178270800665939[233] = 0;
   out_2871178270800665939[234] = 0;
   out_2871178270800665939[235] = 0;
   out_2871178270800665939[236] = 0;
   out_2871178270800665939[237] = 0;
   out_2871178270800665939[238] = 0;
   out_2871178270800665939[239] = 0;
   out_2871178270800665939[240] = 0;
   out_2871178270800665939[241] = 0;
   out_2871178270800665939[242] = 0;
   out_2871178270800665939[243] = 0;
   out_2871178270800665939[244] = 0;
   out_2871178270800665939[245] = 0;
   out_2871178270800665939[246] = 0;
   out_2871178270800665939[247] = 1;
   out_2871178270800665939[248] = 0;
   out_2871178270800665939[249] = 0;
   out_2871178270800665939[250] = 0;
   out_2871178270800665939[251] = 0;
   out_2871178270800665939[252] = 0;
   out_2871178270800665939[253] = 0;
   out_2871178270800665939[254] = 0;
   out_2871178270800665939[255] = 0;
   out_2871178270800665939[256] = 0;
   out_2871178270800665939[257] = 0;
   out_2871178270800665939[258] = 0;
   out_2871178270800665939[259] = 0;
   out_2871178270800665939[260] = 0;
   out_2871178270800665939[261] = 0;
   out_2871178270800665939[262] = 0;
   out_2871178270800665939[263] = 0;
   out_2871178270800665939[264] = 0;
   out_2871178270800665939[265] = 0;
   out_2871178270800665939[266] = 1;
   out_2871178270800665939[267] = 0;
   out_2871178270800665939[268] = 0;
   out_2871178270800665939[269] = 0;
   out_2871178270800665939[270] = 0;
   out_2871178270800665939[271] = 0;
   out_2871178270800665939[272] = 0;
   out_2871178270800665939[273] = 0;
   out_2871178270800665939[274] = 0;
   out_2871178270800665939[275] = 0;
   out_2871178270800665939[276] = 0;
   out_2871178270800665939[277] = 0;
   out_2871178270800665939[278] = 0;
   out_2871178270800665939[279] = 0;
   out_2871178270800665939[280] = 0;
   out_2871178270800665939[281] = 0;
   out_2871178270800665939[282] = 0;
   out_2871178270800665939[283] = 0;
   out_2871178270800665939[284] = 0;
   out_2871178270800665939[285] = 1;
   out_2871178270800665939[286] = 0;
   out_2871178270800665939[287] = 0;
   out_2871178270800665939[288] = 0;
   out_2871178270800665939[289] = 0;
   out_2871178270800665939[290] = 0;
   out_2871178270800665939[291] = 0;
   out_2871178270800665939[292] = 0;
   out_2871178270800665939[293] = 0;
   out_2871178270800665939[294] = 0;
   out_2871178270800665939[295] = 0;
   out_2871178270800665939[296] = 0;
   out_2871178270800665939[297] = 0;
   out_2871178270800665939[298] = 0;
   out_2871178270800665939[299] = 0;
   out_2871178270800665939[300] = 0;
   out_2871178270800665939[301] = 0;
   out_2871178270800665939[302] = 0;
   out_2871178270800665939[303] = 0;
   out_2871178270800665939[304] = 1;
   out_2871178270800665939[305] = 0;
   out_2871178270800665939[306] = 0;
   out_2871178270800665939[307] = 0;
   out_2871178270800665939[308] = 0;
   out_2871178270800665939[309] = 0;
   out_2871178270800665939[310] = 0;
   out_2871178270800665939[311] = 0;
   out_2871178270800665939[312] = 0;
   out_2871178270800665939[313] = 0;
   out_2871178270800665939[314] = 0;
   out_2871178270800665939[315] = 0;
   out_2871178270800665939[316] = 0;
   out_2871178270800665939[317] = 0;
   out_2871178270800665939[318] = 0;
   out_2871178270800665939[319] = 0;
   out_2871178270800665939[320] = 0;
   out_2871178270800665939[321] = 0;
   out_2871178270800665939[322] = 0;
   out_2871178270800665939[323] = 1;
}
void h_4(double *state, double *unused, double *out_3846978595453462265) {
   out_3846978595453462265[0] = state[6] + state[9];
   out_3846978595453462265[1] = state[7] + state[10];
   out_3846978595453462265[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_2510217775991991567) {
   out_2510217775991991567[0] = 0;
   out_2510217775991991567[1] = 0;
   out_2510217775991991567[2] = 0;
   out_2510217775991991567[3] = 0;
   out_2510217775991991567[4] = 0;
   out_2510217775991991567[5] = 0;
   out_2510217775991991567[6] = 1;
   out_2510217775991991567[7] = 0;
   out_2510217775991991567[8] = 0;
   out_2510217775991991567[9] = 1;
   out_2510217775991991567[10] = 0;
   out_2510217775991991567[11] = 0;
   out_2510217775991991567[12] = 0;
   out_2510217775991991567[13] = 0;
   out_2510217775991991567[14] = 0;
   out_2510217775991991567[15] = 0;
   out_2510217775991991567[16] = 0;
   out_2510217775991991567[17] = 0;
   out_2510217775991991567[18] = 0;
   out_2510217775991991567[19] = 0;
   out_2510217775991991567[20] = 0;
   out_2510217775991991567[21] = 0;
   out_2510217775991991567[22] = 0;
   out_2510217775991991567[23] = 0;
   out_2510217775991991567[24] = 0;
   out_2510217775991991567[25] = 1;
   out_2510217775991991567[26] = 0;
   out_2510217775991991567[27] = 0;
   out_2510217775991991567[28] = 1;
   out_2510217775991991567[29] = 0;
   out_2510217775991991567[30] = 0;
   out_2510217775991991567[31] = 0;
   out_2510217775991991567[32] = 0;
   out_2510217775991991567[33] = 0;
   out_2510217775991991567[34] = 0;
   out_2510217775991991567[35] = 0;
   out_2510217775991991567[36] = 0;
   out_2510217775991991567[37] = 0;
   out_2510217775991991567[38] = 0;
   out_2510217775991991567[39] = 0;
   out_2510217775991991567[40] = 0;
   out_2510217775991991567[41] = 0;
   out_2510217775991991567[42] = 0;
   out_2510217775991991567[43] = 0;
   out_2510217775991991567[44] = 1;
   out_2510217775991991567[45] = 0;
   out_2510217775991991567[46] = 0;
   out_2510217775991991567[47] = 1;
   out_2510217775991991567[48] = 0;
   out_2510217775991991567[49] = 0;
   out_2510217775991991567[50] = 0;
   out_2510217775991991567[51] = 0;
   out_2510217775991991567[52] = 0;
   out_2510217775991991567[53] = 0;
}
void h_10(double *state, double *unused, double *out_7920856264594772367) {
   out_7920856264594772367[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_7920856264594772367[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_7920856264594772367[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8226281178388112719) {
   out_8226281178388112719[0] = 0;
   out_8226281178388112719[1] = 9.8100000000000005*cos(state[1]);
   out_8226281178388112719[2] = 0;
   out_8226281178388112719[3] = 0;
   out_8226281178388112719[4] = -state[8];
   out_8226281178388112719[5] = state[7];
   out_8226281178388112719[6] = 0;
   out_8226281178388112719[7] = state[5];
   out_8226281178388112719[8] = -state[4];
   out_8226281178388112719[9] = 0;
   out_8226281178388112719[10] = 0;
   out_8226281178388112719[11] = 0;
   out_8226281178388112719[12] = 1;
   out_8226281178388112719[13] = 0;
   out_8226281178388112719[14] = 0;
   out_8226281178388112719[15] = 1;
   out_8226281178388112719[16] = 0;
   out_8226281178388112719[17] = 0;
   out_8226281178388112719[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8226281178388112719[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8226281178388112719[20] = 0;
   out_8226281178388112719[21] = state[8];
   out_8226281178388112719[22] = 0;
   out_8226281178388112719[23] = -state[6];
   out_8226281178388112719[24] = -state[5];
   out_8226281178388112719[25] = 0;
   out_8226281178388112719[26] = state[3];
   out_8226281178388112719[27] = 0;
   out_8226281178388112719[28] = 0;
   out_8226281178388112719[29] = 0;
   out_8226281178388112719[30] = 0;
   out_8226281178388112719[31] = 1;
   out_8226281178388112719[32] = 0;
   out_8226281178388112719[33] = 0;
   out_8226281178388112719[34] = 1;
   out_8226281178388112719[35] = 0;
   out_8226281178388112719[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8226281178388112719[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8226281178388112719[38] = 0;
   out_8226281178388112719[39] = -state[7];
   out_8226281178388112719[40] = state[6];
   out_8226281178388112719[41] = 0;
   out_8226281178388112719[42] = state[4];
   out_8226281178388112719[43] = -state[3];
   out_8226281178388112719[44] = 0;
   out_8226281178388112719[45] = 0;
   out_8226281178388112719[46] = 0;
   out_8226281178388112719[47] = 0;
   out_8226281178388112719[48] = 0;
   out_8226281178388112719[49] = 0;
   out_8226281178388112719[50] = 1;
   out_8226281178388112719[51] = 0;
   out_8226281178388112719[52] = 0;
   out_8226281178388112719[53] = 1;
}
void h_13(double *state, double *unused, double *out_8094608070185368102) {
   out_8094608070185368102[0] = state[3];
   out_8094608070185368102[1] = state[4];
   out_8094608070185368102[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8325895089400859120) {
   out_8325895089400859120[0] = 0;
   out_8325895089400859120[1] = 0;
   out_8325895089400859120[2] = 0;
   out_8325895089400859120[3] = 1;
   out_8325895089400859120[4] = 0;
   out_8325895089400859120[5] = 0;
   out_8325895089400859120[6] = 0;
   out_8325895089400859120[7] = 0;
   out_8325895089400859120[8] = 0;
   out_8325895089400859120[9] = 0;
   out_8325895089400859120[10] = 0;
   out_8325895089400859120[11] = 0;
   out_8325895089400859120[12] = 0;
   out_8325895089400859120[13] = 0;
   out_8325895089400859120[14] = 0;
   out_8325895089400859120[15] = 0;
   out_8325895089400859120[16] = 0;
   out_8325895089400859120[17] = 0;
   out_8325895089400859120[18] = 0;
   out_8325895089400859120[19] = 0;
   out_8325895089400859120[20] = 0;
   out_8325895089400859120[21] = 0;
   out_8325895089400859120[22] = 1;
   out_8325895089400859120[23] = 0;
   out_8325895089400859120[24] = 0;
   out_8325895089400859120[25] = 0;
   out_8325895089400859120[26] = 0;
   out_8325895089400859120[27] = 0;
   out_8325895089400859120[28] = 0;
   out_8325895089400859120[29] = 0;
   out_8325895089400859120[30] = 0;
   out_8325895089400859120[31] = 0;
   out_8325895089400859120[32] = 0;
   out_8325895089400859120[33] = 0;
   out_8325895089400859120[34] = 0;
   out_8325895089400859120[35] = 0;
   out_8325895089400859120[36] = 0;
   out_8325895089400859120[37] = 0;
   out_8325895089400859120[38] = 0;
   out_8325895089400859120[39] = 0;
   out_8325895089400859120[40] = 0;
   out_8325895089400859120[41] = 1;
   out_8325895089400859120[42] = 0;
   out_8325895089400859120[43] = 0;
   out_8325895089400859120[44] = 0;
   out_8325895089400859120[45] = 0;
   out_8325895089400859120[46] = 0;
   out_8325895089400859120[47] = 0;
   out_8325895089400859120[48] = 0;
   out_8325895089400859120[49] = 0;
   out_8325895089400859120[50] = 0;
   out_8325895089400859120[51] = 0;
   out_8325895089400859120[52] = 0;
   out_8325895089400859120[53] = 0;
}
void h_14(double *state, double *unused, double *out_1490158875401441001) {
   out_1490158875401441001[0] = state[6];
   out_1490158875401441001[1] = state[7];
   out_1490158875401441001[2] = state[8];
}
void H_14(double *state, double *unused, double *out_572570656303380729) {
   out_572570656303380729[0] = 0;
   out_572570656303380729[1] = 0;
   out_572570656303380729[2] = 0;
   out_572570656303380729[3] = 0;
   out_572570656303380729[4] = 0;
   out_572570656303380729[5] = 0;
   out_572570656303380729[6] = 1;
   out_572570656303380729[7] = 0;
   out_572570656303380729[8] = 0;
   out_572570656303380729[9] = 0;
   out_572570656303380729[10] = 0;
   out_572570656303380729[11] = 0;
   out_572570656303380729[12] = 0;
   out_572570656303380729[13] = 0;
   out_572570656303380729[14] = 0;
   out_572570656303380729[15] = 0;
   out_572570656303380729[16] = 0;
   out_572570656303380729[17] = 0;
   out_572570656303380729[18] = 0;
   out_572570656303380729[19] = 0;
   out_572570656303380729[20] = 0;
   out_572570656303380729[21] = 0;
   out_572570656303380729[22] = 0;
   out_572570656303380729[23] = 0;
   out_572570656303380729[24] = 0;
   out_572570656303380729[25] = 1;
   out_572570656303380729[26] = 0;
   out_572570656303380729[27] = 0;
   out_572570656303380729[28] = 0;
   out_572570656303380729[29] = 0;
   out_572570656303380729[30] = 0;
   out_572570656303380729[31] = 0;
   out_572570656303380729[32] = 0;
   out_572570656303380729[33] = 0;
   out_572570656303380729[34] = 0;
   out_572570656303380729[35] = 0;
   out_572570656303380729[36] = 0;
   out_572570656303380729[37] = 0;
   out_572570656303380729[38] = 0;
   out_572570656303380729[39] = 0;
   out_572570656303380729[40] = 0;
   out_572570656303380729[41] = 0;
   out_572570656303380729[42] = 0;
   out_572570656303380729[43] = 0;
   out_572570656303380729[44] = 1;
   out_572570656303380729[45] = 0;
   out_572570656303380729[46] = 0;
   out_572570656303380729[47] = 0;
   out_572570656303380729[48] = 0;
   out_572570656303380729[49] = 0;
   out_572570656303380729[50] = 0;
   out_572570656303380729[51] = 0;
   out_572570656303380729[52] = 0;
   out_572570656303380729[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_2355293272416553220) {
  err_fun(nom_x, delta_x, out_2355293272416553220);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4800523972292248179) {
  inv_err_fun(nom_x, true_x, out_4800523972292248179);
}
void pose_H_mod_fun(double *state, double *out_1756056773937278960) {
  H_mod_fun(state, out_1756056773937278960);
}
void pose_f_fun(double *state, double dt, double *out_4431905570801982118) {
  f_fun(state,  dt, out_4431905570801982118);
}
void pose_F_fun(double *state, double dt, double *out_2871178270800665939) {
  F_fun(state,  dt, out_2871178270800665939);
}
void pose_h_4(double *state, double *unused, double *out_3846978595453462265) {
  h_4(state, unused, out_3846978595453462265);
}
void pose_H_4(double *state, double *unused, double *out_2510217775991991567) {
  H_4(state, unused, out_2510217775991991567);
}
void pose_h_10(double *state, double *unused, double *out_7920856264594772367) {
  h_10(state, unused, out_7920856264594772367);
}
void pose_H_10(double *state, double *unused, double *out_8226281178388112719) {
  H_10(state, unused, out_8226281178388112719);
}
void pose_h_13(double *state, double *unused, double *out_8094608070185368102) {
  h_13(state, unused, out_8094608070185368102);
}
void pose_H_13(double *state, double *unused, double *out_8325895089400859120) {
  H_13(state, unused, out_8325895089400859120);
}
void pose_h_14(double *state, double *unused, double *out_1490158875401441001) {
  h_14(state, unused, out_1490158875401441001);
}
void pose_H_14(double *state, double *unused, double *out_572570656303380729) {
  H_14(state, unused, out_572570656303380729);
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
