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
void err_fun(double *nom_x, double *delta_x, double *out_4967863734907407968) {
   out_4967863734907407968[0] = delta_x[0] + nom_x[0];
   out_4967863734907407968[1] = delta_x[1] + nom_x[1];
   out_4967863734907407968[2] = delta_x[2] + nom_x[2];
   out_4967863734907407968[3] = delta_x[3] + nom_x[3];
   out_4967863734907407968[4] = delta_x[4] + nom_x[4];
   out_4967863734907407968[5] = delta_x[5] + nom_x[5];
   out_4967863734907407968[6] = delta_x[6] + nom_x[6];
   out_4967863734907407968[7] = delta_x[7] + nom_x[7];
   out_4967863734907407968[8] = delta_x[8] + nom_x[8];
   out_4967863734907407968[9] = delta_x[9] + nom_x[9];
   out_4967863734907407968[10] = delta_x[10] + nom_x[10];
   out_4967863734907407968[11] = delta_x[11] + nom_x[11];
   out_4967863734907407968[12] = delta_x[12] + nom_x[12];
   out_4967863734907407968[13] = delta_x[13] + nom_x[13];
   out_4967863734907407968[14] = delta_x[14] + nom_x[14];
   out_4967863734907407968[15] = delta_x[15] + nom_x[15];
   out_4967863734907407968[16] = delta_x[16] + nom_x[16];
   out_4967863734907407968[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_554301816764323460) {
   out_554301816764323460[0] = -nom_x[0] + true_x[0];
   out_554301816764323460[1] = -nom_x[1] + true_x[1];
   out_554301816764323460[2] = -nom_x[2] + true_x[2];
   out_554301816764323460[3] = -nom_x[3] + true_x[3];
   out_554301816764323460[4] = -nom_x[4] + true_x[4];
   out_554301816764323460[5] = -nom_x[5] + true_x[5];
   out_554301816764323460[6] = -nom_x[6] + true_x[6];
   out_554301816764323460[7] = -nom_x[7] + true_x[7];
   out_554301816764323460[8] = -nom_x[8] + true_x[8];
   out_554301816764323460[9] = -nom_x[9] + true_x[9];
   out_554301816764323460[10] = -nom_x[10] + true_x[10];
   out_554301816764323460[11] = -nom_x[11] + true_x[11];
   out_554301816764323460[12] = -nom_x[12] + true_x[12];
   out_554301816764323460[13] = -nom_x[13] + true_x[13];
   out_554301816764323460[14] = -nom_x[14] + true_x[14];
   out_554301816764323460[15] = -nom_x[15] + true_x[15];
   out_554301816764323460[16] = -nom_x[16] + true_x[16];
   out_554301816764323460[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_3047027985808074405) {
   out_3047027985808074405[0] = 1.0;
   out_3047027985808074405[1] = 0.0;
   out_3047027985808074405[2] = 0.0;
   out_3047027985808074405[3] = 0.0;
   out_3047027985808074405[4] = 0.0;
   out_3047027985808074405[5] = 0.0;
   out_3047027985808074405[6] = 0.0;
   out_3047027985808074405[7] = 0.0;
   out_3047027985808074405[8] = 0.0;
   out_3047027985808074405[9] = 0.0;
   out_3047027985808074405[10] = 0.0;
   out_3047027985808074405[11] = 0.0;
   out_3047027985808074405[12] = 0.0;
   out_3047027985808074405[13] = 0.0;
   out_3047027985808074405[14] = 0.0;
   out_3047027985808074405[15] = 0.0;
   out_3047027985808074405[16] = 0.0;
   out_3047027985808074405[17] = 0.0;
   out_3047027985808074405[18] = 0.0;
   out_3047027985808074405[19] = 1.0;
   out_3047027985808074405[20] = 0.0;
   out_3047027985808074405[21] = 0.0;
   out_3047027985808074405[22] = 0.0;
   out_3047027985808074405[23] = 0.0;
   out_3047027985808074405[24] = 0.0;
   out_3047027985808074405[25] = 0.0;
   out_3047027985808074405[26] = 0.0;
   out_3047027985808074405[27] = 0.0;
   out_3047027985808074405[28] = 0.0;
   out_3047027985808074405[29] = 0.0;
   out_3047027985808074405[30] = 0.0;
   out_3047027985808074405[31] = 0.0;
   out_3047027985808074405[32] = 0.0;
   out_3047027985808074405[33] = 0.0;
   out_3047027985808074405[34] = 0.0;
   out_3047027985808074405[35] = 0.0;
   out_3047027985808074405[36] = 0.0;
   out_3047027985808074405[37] = 0.0;
   out_3047027985808074405[38] = 1.0;
   out_3047027985808074405[39] = 0.0;
   out_3047027985808074405[40] = 0.0;
   out_3047027985808074405[41] = 0.0;
   out_3047027985808074405[42] = 0.0;
   out_3047027985808074405[43] = 0.0;
   out_3047027985808074405[44] = 0.0;
   out_3047027985808074405[45] = 0.0;
   out_3047027985808074405[46] = 0.0;
   out_3047027985808074405[47] = 0.0;
   out_3047027985808074405[48] = 0.0;
   out_3047027985808074405[49] = 0.0;
   out_3047027985808074405[50] = 0.0;
   out_3047027985808074405[51] = 0.0;
   out_3047027985808074405[52] = 0.0;
   out_3047027985808074405[53] = 0.0;
   out_3047027985808074405[54] = 0.0;
   out_3047027985808074405[55] = 0.0;
   out_3047027985808074405[56] = 0.0;
   out_3047027985808074405[57] = 1.0;
   out_3047027985808074405[58] = 0.0;
   out_3047027985808074405[59] = 0.0;
   out_3047027985808074405[60] = 0.0;
   out_3047027985808074405[61] = 0.0;
   out_3047027985808074405[62] = 0.0;
   out_3047027985808074405[63] = 0.0;
   out_3047027985808074405[64] = 0.0;
   out_3047027985808074405[65] = 0.0;
   out_3047027985808074405[66] = 0.0;
   out_3047027985808074405[67] = 0.0;
   out_3047027985808074405[68] = 0.0;
   out_3047027985808074405[69] = 0.0;
   out_3047027985808074405[70] = 0.0;
   out_3047027985808074405[71] = 0.0;
   out_3047027985808074405[72] = 0.0;
   out_3047027985808074405[73] = 0.0;
   out_3047027985808074405[74] = 0.0;
   out_3047027985808074405[75] = 0.0;
   out_3047027985808074405[76] = 1.0;
   out_3047027985808074405[77] = 0.0;
   out_3047027985808074405[78] = 0.0;
   out_3047027985808074405[79] = 0.0;
   out_3047027985808074405[80] = 0.0;
   out_3047027985808074405[81] = 0.0;
   out_3047027985808074405[82] = 0.0;
   out_3047027985808074405[83] = 0.0;
   out_3047027985808074405[84] = 0.0;
   out_3047027985808074405[85] = 0.0;
   out_3047027985808074405[86] = 0.0;
   out_3047027985808074405[87] = 0.0;
   out_3047027985808074405[88] = 0.0;
   out_3047027985808074405[89] = 0.0;
   out_3047027985808074405[90] = 0.0;
   out_3047027985808074405[91] = 0.0;
   out_3047027985808074405[92] = 0.0;
   out_3047027985808074405[93] = 0.0;
   out_3047027985808074405[94] = 0.0;
   out_3047027985808074405[95] = 1.0;
   out_3047027985808074405[96] = 0.0;
   out_3047027985808074405[97] = 0.0;
   out_3047027985808074405[98] = 0.0;
   out_3047027985808074405[99] = 0.0;
   out_3047027985808074405[100] = 0.0;
   out_3047027985808074405[101] = 0.0;
   out_3047027985808074405[102] = 0.0;
   out_3047027985808074405[103] = 0.0;
   out_3047027985808074405[104] = 0.0;
   out_3047027985808074405[105] = 0.0;
   out_3047027985808074405[106] = 0.0;
   out_3047027985808074405[107] = 0.0;
   out_3047027985808074405[108] = 0.0;
   out_3047027985808074405[109] = 0.0;
   out_3047027985808074405[110] = 0.0;
   out_3047027985808074405[111] = 0.0;
   out_3047027985808074405[112] = 0.0;
   out_3047027985808074405[113] = 0.0;
   out_3047027985808074405[114] = 1.0;
   out_3047027985808074405[115] = 0.0;
   out_3047027985808074405[116] = 0.0;
   out_3047027985808074405[117] = 0.0;
   out_3047027985808074405[118] = 0.0;
   out_3047027985808074405[119] = 0.0;
   out_3047027985808074405[120] = 0.0;
   out_3047027985808074405[121] = 0.0;
   out_3047027985808074405[122] = 0.0;
   out_3047027985808074405[123] = 0.0;
   out_3047027985808074405[124] = 0.0;
   out_3047027985808074405[125] = 0.0;
   out_3047027985808074405[126] = 0.0;
   out_3047027985808074405[127] = 0.0;
   out_3047027985808074405[128] = 0.0;
   out_3047027985808074405[129] = 0.0;
   out_3047027985808074405[130] = 0.0;
   out_3047027985808074405[131] = 0.0;
   out_3047027985808074405[132] = 0.0;
   out_3047027985808074405[133] = 1.0;
   out_3047027985808074405[134] = 0.0;
   out_3047027985808074405[135] = 0.0;
   out_3047027985808074405[136] = 0.0;
   out_3047027985808074405[137] = 0.0;
   out_3047027985808074405[138] = 0.0;
   out_3047027985808074405[139] = 0.0;
   out_3047027985808074405[140] = 0.0;
   out_3047027985808074405[141] = 0.0;
   out_3047027985808074405[142] = 0.0;
   out_3047027985808074405[143] = 0.0;
   out_3047027985808074405[144] = 0.0;
   out_3047027985808074405[145] = 0.0;
   out_3047027985808074405[146] = 0.0;
   out_3047027985808074405[147] = 0.0;
   out_3047027985808074405[148] = 0.0;
   out_3047027985808074405[149] = 0.0;
   out_3047027985808074405[150] = 0.0;
   out_3047027985808074405[151] = 0.0;
   out_3047027985808074405[152] = 1.0;
   out_3047027985808074405[153] = 0.0;
   out_3047027985808074405[154] = 0.0;
   out_3047027985808074405[155] = 0.0;
   out_3047027985808074405[156] = 0.0;
   out_3047027985808074405[157] = 0.0;
   out_3047027985808074405[158] = 0.0;
   out_3047027985808074405[159] = 0.0;
   out_3047027985808074405[160] = 0.0;
   out_3047027985808074405[161] = 0.0;
   out_3047027985808074405[162] = 0.0;
   out_3047027985808074405[163] = 0.0;
   out_3047027985808074405[164] = 0.0;
   out_3047027985808074405[165] = 0.0;
   out_3047027985808074405[166] = 0.0;
   out_3047027985808074405[167] = 0.0;
   out_3047027985808074405[168] = 0.0;
   out_3047027985808074405[169] = 0.0;
   out_3047027985808074405[170] = 0.0;
   out_3047027985808074405[171] = 1.0;
   out_3047027985808074405[172] = 0.0;
   out_3047027985808074405[173] = 0.0;
   out_3047027985808074405[174] = 0.0;
   out_3047027985808074405[175] = 0.0;
   out_3047027985808074405[176] = 0.0;
   out_3047027985808074405[177] = 0.0;
   out_3047027985808074405[178] = 0.0;
   out_3047027985808074405[179] = 0.0;
   out_3047027985808074405[180] = 0.0;
   out_3047027985808074405[181] = 0.0;
   out_3047027985808074405[182] = 0.0;
   out_3047027985808074405[183] = 0.0;
   out_3047027985808074405[184] = 0.0;
   out_3047027985808074405[185] = 0.0;
   out_3047027985808074405[186] = 0.0;
   out_3047027985808074405[187] = 0.0;
   out_3047027985808074405[188] = 0.0;
   out_3047027985808074405[189] = 0.0;
   out_3047027985808074405[190] = 1.0;
   out_3047027985808074405[191] = 0.0;
   out_3047027985808074405[192] = 0.0;
   out_3047027985808074405[193] = 0.0;
   out_3047027985808074405[194] = 0.0;
   out_3047027985808074405[195] = 0.0;
   out_3047027985808074405[196] = 0.0;
   out_3047027985808074405[197] = 0.0;
   out_3047027985808074405[198] = 0.0;
   out_3047027985808074405[199] = 0.0;
   out_3047027985808074405[200] = 0.0;
   out_3047027985808074405[201] = 0.0;
   out_3047027985808074405[202] = 0.0;
   out_3047027985808074405[203] = 0.0;
   out_3047027985808074405[204] = 0.0;
   out_3047027985808074405[205] = 0.0;
   out_3047027985808074405[206] = 0.0;
   out_3047027985808074405[207] = 0.0;
   out_3047027985808074405[208] = 0.0;
   out_3047027985808074405[209] = 1.0;
   out_3047027985808074405[210] = 0.0;
   out_3047027985808074405[211] = 0.0;
   out_3047027985808074405[212] = 0.0;
   out_3047027985808074405[213] = 0.0;
   out_3047027985808074405[214] = 0.0;
   out_3047027985808074405[215] = 0.0;
   out_3047027985808074405[216] = 0.0;
   out_3047027985808074405[217] = 0.0;
   out_3047027985808074405[218] = 0.0;
   out_3047027985808074405[219] = 0.0;
   out_3047027985808074405[220] = 0.0;
   out_3047027985808074405[221] = 0.0;
   out_3047027985808074405[222] = 0.0;
   out_3047027985808074405[223] = 0.0;
   out_3047027985808074405[224] = 0.0;
   out_3047027985808074405[225] = 0.0;
   out_3047027985808074405[226] = 0.0;
   out_3047027985808074405[227] = 0.0;
   out_3047027985808074405[228] = 1.0;
   out_3047027985808074405[229] = 0.0;
   out_3047027985808074405[230] = 0.0;
   out_3047027985808074405[231] = 0.0;
   out_3047027985808074405[232] = 0.0;
   out_3047027985808074405[233] = 0.0;
   out_3047027985808074405[234] = 0.0;
   out_3047027985808074405[235] = 0.0;
   out_3047027985808074405[236] = 0.0;
   out_3047027985808074405[237] = 0.0;
   out_3047027985808074405[238] = 0.0;
   out_3047027985808074405[239] = 0.0;
   out_3047027985808074405[240] = 0.0;
   out_3047027985808074405[241] = 0.0;
   out_3047027985808074405[242] = 0.0;
   out_3047027985808074405[243] = 0.0;
   out_3047027985808074405[244] = 0.0;
   out_3047027985808074405[245] = 0.0;
   out_3047027985808074405[246] = 0.0;
   out_3047027985808074405[247] = 1.0;
   out_3047027985808074405[248] = 0.0;
   out_3047027985808074405[249] = 0.0;
   out_3047027985808074405[250] = 0.0;
   out_3047027985808074405[251] = 0.0;
   out_3047027985808074405[252] = 0.0;
   out_3047027985808074405[253] = 0.0;
   out_3047027985808074405[254] = 0.0;
   out_3047027985808074405[255] = 0.0;
   out_3047027985808074405[256] = 0.0;
   out_3047027985808074405[257] = 0.0;
   out_3047027985808074405[258] = 0.0;
   out_3047027985808074405[259] = 0.0;
   out_3047027985808074405[260] = 0.0;
   out_3047027985808074405[261] = 0.0;
   out_3047027985808074405[262] = 0.0;
   out_3047027985808074405[263] = 0.0;
   out_3047027985808074405[264] = 0.0;
   out_3047027985808074405[265] = 0.0;
   out_3047027985808074405[266] = 1.0;
   out_3047027985808074405[267] = 0.0;
   out_3047027985808074405[268] = 0.0;
   out_3047027985808074405[269] = 0.0;
   out_3047027985808074405[270] = 0.0;
   out_3047027985808074405[271] = 0.0;
   out_3047027985808074405[272] = 0.0;
   out_3047027985808074405[273] = 0.0;
   out_3047027985808074405[274] = 0.0;
   out_3047027985808074405[275] = 0.0;
   out_3047027985808074405[276] = 0.0;
   out_3047027985808074405[277] = 0.0;
   out_3047027985808074405[278] = 0.0;
   out_3047027985808074405[279] = 0.0;
   out_3047027985808074405[280] = 0.0;
   out_3047027985808074405[281] = 0.0;
   out_3047027985808074405[282] = 0.0;
   out_3047027985808074405[283] = 0.0;
   out_3047027985808074405[284] = 0.0;
   out_3047027985808074405[285] = 1.0;
   out_3047027985808074405[286] = 0.0;
   out_3047027985808074405[287] = 0.0;
   out_3047027985808074405[288] = 0.0;
   out_3047027985808074405[289] = 0.0;
   out_3047027985808074405[290] = 0.0;
   out_3047027985808074405[291] = 0.0;
   out_3047027985808074405[292] = 0.0;
   out_3047027985808074405[293] = 0.0;
   out_3047027985808074405[294] = 0.0;
   out_3047027985808074405[295] = 0.0;
   out_3047027985808074405[296] = 0.0;
   out_3047027985808074405[297] = 0.0;
   out_3047027985808074405[298] = 0.0;
   out_3047027985808074405[299] = 0.0;
   out_3047027985808074405[300] = 0.0;
   out_3047027985808074405[301] = 0.0;
   out_3047027985808074405[302] = 0.0;
   out_3047027985808074405[303] = 0.0;
   out_3047027985808074405[304] = 1.0;
   out_3047027985808074405[305] = 0.0;
   out_3047027985808074405[306] = 0.0;
   out_3047027985808074405[307] = 0.0;
   out_3047027985808074405[308] = 0.0;
   out_3047027985808074405[309] = 0.0;
   out_3047027985808074405[310] = 0.0;
   out_3047027985808074405[311] = 0.0;
   out_3047027985808074405[312] = 0.0;
   out_3047027985808074405[313] = 0.0;
   out_3047027985808074405[314] = 0.0;
   out_3047027985808074405[315] = 0.0;
   out_3047027985808074405[316] = 0.0;
   out_3047027985808074405[317] = 0.0;
   out_3047027985808074405[318] = 0.0;
   out_3047027985808074405[319] = 0.0;
   out_3047027985808074405[320] = 0.0;
   out_3047027985808074405[321] = 0.0;
   out_3047027985808074405[322] = 0.0;
   out_3047027985808074405[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_986492010673501731) {
   out_986492010673501731[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_986492010673501731[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_986492010673501731[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_986492010673501731[3] = dt*state[12] + state[3];
   out_986492010673501731[4] = dt*state[13] + state[4];
   out_986492010673501731[5] = dt*state[14] + state[5];
   out_986492010673501731[6] = state[6];
   out_986492010673501731[7] = state[7];
   out_986492010673501731[8] = state[8];
   out_986492010673501731[9] = state[9];
   out_986492010673501731[10] = state[10];
   out_986492010673501731[11] = state[11];
   out_986492010673501731[12] = state[12];
   out_986492010673501731[13] = state[13];
   out_986492010673501731[14] = state[14];
   out_986492010673501731[15] = state[15];
   out_986492010673501731[16] = state[16];
   out_986492010673501731[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4336070434649428420) {
   out_4336070434649428420[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4336070434649428420[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4336070434649428420[2] = 0;
   out_4336070434649428420[3] = 0;
   out_4336070434649428420[4] = 0;
   out_4336070434649428420[5] = 0;
   out_4336070434649428420[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4336070434649428420[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4336070434649428420[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4336070434649428420[9] = 0;
   out_4336070434649428420[10] = 0;
   out_4336070434649428420[11] = 0;
   out_4336070434649428420[12] = 0;
   out_4336070434649428420[13] = 0;
   out_4336070434649428420[14] = 0;
   out_4336070434649428420[15] = 0;
   out_4336070434649428420[16] = 0;
   out_4336070434649428420[17] = 0;
   out_4336070434649428420[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4336070434649428420[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4336070434649428420[20] = 0;
   out_4336070434649428420[21] = 0;
   out_4336070434649428420[22] = 0;
   out_4336070434649428420[23] = 0;
   out_4336070434649428420[24] = 0;
   out_4336070434649428420[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4336070434649428420[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4336070434649428420[27] = 0;
   out_4336070434649428420[28] = 0;
   out_4336070434649428420[29] = 0;
   out_4336070434649428420[30] = 0;
   out_4336070434649428420[31] = 0;
   out_4336070434649428420[32] = 0;
   out_4336070434649428420[33] = 0;
   out_4336070434649428420[34] = 0;
   out_4336070434649428420[35] = 0;
   out_4336070434649428420[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4336070434649428420[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4336070434649428420[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4336070434649428420[39] = 0;
   out_4336070434649428420[40] = 0;
   out_4336070434649428420[41] = 0;
   out_4336070434649428420[42] = 0;
   out_4336070434649428420[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4336070434649428420[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4336070434649428420[45] = 0;
   out_4336070434649428420[46] = 0;
   out_4336070434649428420[47] = 0;
   out_4336070434649428420[48] = 0;
   out_4336070434649428420[49] = 0;
   out_4336070434649428420[50] = 0;
   out_4336070434649428420[51] = 0;
   out_4336070434649428420[52] = 0;
   out_4336070434649428420[53] = 0;
   out_4336070434649428420[54] = 0;
   out_4336070434649428420[55] = 0;
   out_4336070434649428420[56] = 0;
   out_4336070434649428420[57] = 1;
   out_4336070434649428420[58] = 0;
   out_4336070434649428420[59] = 0;
   out_4336070434649428420[60] = 0;
   out_4336070434649428420[61] = 0;
   out_4336070434649428420[62] = 0;
   out_4336070434649428420[63] = 0;
   out_4336070434649428420[64] = 0;
   out_4336070434649428420[65] = 0;
   out_4336070434649428420[66] = dt;
   out_4336070434649428420[67] = 0;
   out_4336070434649428420[68] = 0;
   out_4336070434649428420[69] = 0;
   out_4336070434649428420[70] = 0;
   out_4336070434649428420[71] = 0;
   out_4336070434649428420[72] = 0;
   out_4336070434649428420[73] = 0;
   out_4336070434649428420[74] = 0;
   out_4336070434649428420[75] = 0;
   out_4336070434649428420[76] = 1;
   out_4336070434649428420[77] = 0;
   out_4336070434649428420[78] = 0;
   out_4336070434649428420[79] = 0;
   out_4336070434649428420[80] = 0;
   out_4336070434649428420[81] = 0;
   out_4336070434649428420[82] = 0;
   out_4336070434649428420[83] = 0;
   out_4336070434649428420[84] = 0;
   out_4336070434649428420[85] = dt;
   out_4336070434649428420[86] = 0;
   out_4336070434649428420[87] = 0;
   out_4336070434649428420[88] = 0;
   out_4336070434649428420[89] = 0;
   out_4336070434649428420[90] = 0;
   out_4336070434649428420[91] = 0;
   out_4336070434649428420[92] = 0;
   out_4336070434649428420[93] = 0;
   out_4336070434649428420[94] = 0;
   out_4336070434649428420[95] = 1;
   out_4336070434649428420[96] = 0;
   out_4336070434649428420[97] = 0;
   out_4336070434649428420[98] = 0;
   out_4336070434649428420[99] = 0;
   out_4336070434649428420[100] = 0;
   out_4336070434649428420[101] = 0;
   out_4336070434649428420[102] = 0;
   out_4336070434649428420[103] = 0;
   out_4336070434649428420[104] = dt;
   out_4336070434649428420[105] = 0;
   out_4336070434649428420[106] = 0;
   out_4336070434649428420[107] = 0;
   out_4336070434649428420[108] = 0;
   out_4336070434649428420[109] = 0;
   out_4336070434649428420[110] = 0;
   out_4336070434649428420[111] = 0;
   out_4336070434649428420[112] = 0;
   out_4336070434649428420[113] = 0;
   out_4336070434649428420[114] = 1;
   out_4336070434649428420[115] = 0;
   out_4336070434649428420[116] = 0;
   out_4336070434649428420[117] = 0;
   out_4336070434649428420[118] = 0;
   out_4336070434649428420[119] = 0;
   out_4336070434649428420[120] = 0;
   out_4336070434649428420[121] = 0;
   out_4336070434649428420[122] = 0;
   out_4336070434649428420[123] = 0;
   out_4336070434649428420[124] = 0;
   out_4336070434649428420[125] = 0;
   out_4336070434649428420[126] = 0;
   out_4336070434649428420[127] = 0;
   out_4336070434649428420[128] = 0;
   out_4336070434649428420[129] = 0;
   out_4336070434649428420[130] = 0;
   out_4336070434649428420[131] = 0;
   out_4336070434649428420[132] = 0;
   out_4336070434649428420[133] = 1;
   out_4336070434649428420[134] = 0;
   out_4336070434649428420[135] = 0;
   out_4336070434649428420[136] = 0;
   out_4336070434649428420[137] = 0;
   out_4336070434649428420[138] = 0;
   out_4336070434649428420[139] = 0;
   out_4336070434649428420[140] = 0;
   out_4336070434649428420[141] = 0;
   out_4336070434649428420[142] = 0;
   out_4336070434649428420[143] = 0;
   out_4336070434649428420[144] = 0;
   out_4336070434649428420[145] = 0;
   out_4336070434649428420[146] = 0;
   out_4336070434649428420[147] = 0;
   out_4336070434649428420[148] = 0;
   out_4336070434649428420[149] = 0;
   out_4336070434649428420[150] = 0;
   out_4336070434649428420[151] = 0;
   out_4336070434649428420[152] = 1;
   out_4336070434649428420[153] = 0;
   out_4336070434649428420[154] = 0;
   out_4336070434649428420[155] = 0;
   out_4336070434649428420[156] = 0;
   out_4336070434649428420[157] = 0;
   out_4336070434649428420[158] = 0;
   out_4336070434649428420[159] = 0;
   out_4336070434649428420[160] = 0;
   out_4336070434649428420[161] = 0;
   out_4336070434649428420[162] = 0;
   out_4336070434649428420[163] = 0;
   out_4336070434649428420[164] = 0;
   out_4336070434649428420[165] = 0;
   out_4336070434649428420[166] = 0;
   out_4336070434649428420[167] = 0;
   out_4336070434649428420[168] = 0;
   out_4336070434649428420[169] = 0;
   out_4336070434649428420[170] = 0;
   out_4336070434649428420[171] = 1;
   out_4336070434649428420[172] = 0;
   out_4336070434649428420[173] = 0;
   out_4336070434649428420[174] = 0;
   out_4336070434649428420[175] = 0;
   out_4336070434649428420[176] = 0;
   out_4336070434649428420[177] = 0;
   out_4336070434649428420[178] = 0;
   out_4336070434649428420[179] = 0;
   out_4336070434649428420[180] = 0;
   out_4336070434649428420[181] = 0;
   out_4336070434649428420[182] = 0;
   out_4336070434649428420[183] = 0;
   out_4336070434649428420[184] = 0;
   out_4336070434649428420[185] = 0;
   out_4336070434649428420[186] = 0;
   out_4336070434649428420[187] = 0;
   out_4336070434649428420[188] = 0;
   out_4336070434649428420[189] = 0;
   out_4336070434649428420[190] = 1;
   out_4336070434649428420[191] = 0;
   out_4336070434649428420[192] = 0;
   out_4336070434649428420[193] = 0;
   out_4336070434649428420[194] = 0;
   out_4336070434649428420[195] = 0;
   out_4336070434649428420[196] = 0;
   out_4336070434649428420[197] = 0;
   out_4336070434649428420[198] = 0;
   out_4336070434649428420[199] = 0;
   out_4336070434649428420[200] = 0;
   out_4336070434649428420[201] = 0;
   out_4336070434649428420[202] = 0;
   out_4336070434649428420[203] = 0;
   out_4336070434649428420[204] = 0;
   out_4336070434649428420[205] = 0;
   out_4336070434649428420[206] = 0;
   out_4336070434649428420[207] = 0;
   out_4336070434649428420[208] = 0;
   out_4336070434649428420[209] = 1;
   out_4336070434649428420[210] = 0;
   out_4336070434649428420[211] = 0;
   out_4336070434649428420[212] = 0;
   out_4336070434649428420[213] = 0;
   out_4336070434649428420[214] = 0;
   out_4336070434649428420[215] = 0;
   out_4336070434649428420[216] = 0;
   out_4336070434649428420[217] = 0;
   out_4336070434649428420[218] = 0;
   out_4336070434649428420[219] = 0;
   out_4336070434649428420[220] = 0;
   out_4336070434649428420[221] = 0;
   out_4336070434649428420[222] = 0;
   out_4336070434649428420[223] = 0;
   out_4336070434649428420[224] = 0;
   out_4336070434649428420[225] = 0;
   out_4336070434649428420[226] = 0;
   out_4336070434649428420[227] = 0;
   out_4336070434649428420[228] = 1;
   out_4336070434649428420[229] = 0;
   out_4336070434649428420[230] = 0;
   out_4336070434649428420[231] = 0;
   out_4336070434649428420[232] = 0;
   out_4336070434649428420[233] = 0;
   out_4336070434649428420[234] = 0;
   out_4336070434649428420[235] = 0;
   out_4336070434649428420[236] = 0;
   out_4336070434649428420[237] = 0;
   out_4336070434649428420[238] = 0;
   out_4336070434649428420[239] = 0;
   out_4336070434649428420[240] = 0;
   out_4336070434649428420[241] = 0;
   out_4336070434649428420[242] = 0;
   out_4336070434649428420[243] = 0;
   out_4336070434649428420[244] = 0;
   out_4336070434649428420[245] = 0;
   out_4336070434649428420[246] = 0;
   out_4336070434649428420[247] = 1;
   out_4336070434649428420[248] = 0;
   out_4336070434649428420[249] = 0;
   out_4336070434649428420[250] = 0;
   out_4336070434649428420[251] = 0;
   out_4336070434649428420[252] = 0;
   out_4336070434649428420[253] = 0;
   out_4336070434649428420[254] = 0;
   out_4336070434649428420[255] = 0;
   out_4336070434649428420[256] = 0;
   out_4336070434649428420[257] = 0;
   out_4336070434649428420[258] = 0;
   out_4336070434649428420[259] = 0;
   out_4336070434649428420[260] = 0;
   out_4336070434649428420[261] = 0;
   out_4336070434649428420[262] = 0;
   out_4336070434649428420[263] = 0;
   out_4336070434649428420[264] = 0;
   out_4336070434649428420[265] = 0;
   out_4336070434649428420[266] = 1;
   out_4336070434649428420[267] = 0;
   out_4336070434649428420[268] = 0;
   out_4336070434649428420[269] = 0;
   out_4336070434649428420[270] = 0;
   out_4336070434649428420[271] = 0;
   out_4336070434649428420[272] = 0;
   out_4336070434649428420[273] = 0;
   out_4336070434649428420[274] = 0;
   out_4336070434649428420[275] = 0;
   out_4336070434649428420[276] = 0;
   out_4336070434649428420[277] = 0;
   out_4336070434649428420[278] = 0;
   out_4336070434649428420[279] = 0;
   out_4336070434649428420[280] = 0;
   out_4336070434649428420[281] = 0;
   out_4336070434649428420[282] = 0;
   out_4336070434649428420[283] = 0;
   out_4336070434649428420[284] = 0;
   out_4336070434649428420[285] = 1;
   out_4336070434649428420[286] = 0;
   out_4336070434649428420[287] = 0;
   out_4336070434649428420[288] = 0;
   out_4336070434649428420[289] = 0;
   out_4336070434649428420[290] = 0;
   out_4336070434649428420[291] = 0;
   out_4336070434649428420[292] = 0;
   out_4336070434649428420[293] = 0;
   out_4336070434649428420[294] = 0;
   out_4336070434649428420[295] = 0;
   out_4336070434649428420[296] = 0;
   out_4336070434649428420[297] = 0;
   out_4336070434649428420[298] = 0;
   out_4336070434649428420[299] = 0;
   out_4336070434649428420[300] = 0;
   out_4336070434649428420[301] = 0;
   out_4336070434649428420[302] = 0;
   out_4336070434649428420[303] = 0;
   out_4336070434649428420[304] = 1;
   out_4336070434649428420[305] = 0;
   out_4336070434649428420[306] = 0;
   out_4336070434649428420[307] = 0;
   out_4336070434649428420[308] = 0;
   out_4336070434649428420[309] = 0;
   out_4336070434649428420[310] = 0;
   out_4336070434649428420[311] = 0;
   out_4336070434649428420[312] = 0;
   out_4336070434649428420[313] = 0;
   out_4336070434649428420[314] = 0;
   out_4336070434649428420[315] = 0;
   out_4336070434649428420[316] = 0;
   out_4336070434649428420[317] = 0;
   out_4336070434649428420[318] = 0;
   out_4336070434649428420[319] = 0;
   out_4336070434649428420[320] = 0;
   out_4336070434649428420[321] = 0;
   out_4336070434649428420[322] = 0;
   out_4336070434649428420[323] = 1;
}
void h_4(double *state, double *unused, double *out_5526642384709914880) {
   out_5526642384709914880[0] = state[6] + state[9];
   out_5526642384709914880[1] = state[7] + state[10];
   out_5526642384709914880[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_5691168246274914733) {
   out_5691168246274914733[0] = 0;
   out_5691168246274914733[1] = 0;
   out_5691168246274914733[2] = 0;
   out_5691168246274914733[3] = 0;
   out_5691168246274914733[4] = 0;
   out_5691168246274914733[5] = 0;
   out_5691168246274914733[6] = 1;
   out_5691168246274914733[7] = 0;
   out_5691168246274914733[8] = 0;
   out_5691168246274914733[9] = 1;
   out_5691168246274914733[10] = 0;
   out_5691168246274914733[11] = 0;
   out_5691168246274914733[12] = 0;
   out_5691168246274914733[13] = 0;
   out_5691168246274914733[14] = 0;
   out_5691168246274914733[15] = 0;
   out_5691168246274914733[16] = 0;
   out_5691168246274914733[17] = 0;
   out_5691168246274914733[18] = 0;
   out_5691168246274914733[19] = 0;
   out_5691168246274914733[20] = 0;
   out_5691168246274914733[21] = 0;
   out_5691168246274914733[22] = 0;
   out_5691168246274914733[23] = 0;
   out_5691168246274914733[24] = 0;
   out_5691168246274914733[25] = 1;
   out_5691168246274914733[26] = 0;
   out_5691168246274914733[27] = 0;
   out_5691168246274914733[28] = 1;
   out_5691168246274914733[29] = 0;
   out_5691168246274914733[30] = 0;
   out_5691168246274914733[31] = 0;
   out_5691168246274914733[32] = 0;
   out_5691168246274914733[33] = 0;
   out_5691168246274914733[34] = 0;
   out_5691168246274914733[35] = 0;
   out_5691168246274914733[36] = 0;
   out_5691168246274914733[37] = 0;
   out_5691168246274914733[38] = 0;
   out_5691168246274914733[39] = 0;
   out_5691168246274914733[40] = 0;
   out_5691168246274914733[41] = 0;
   out_5691168246274914733[42] = 0;
   out_5691168246274914733[43] = 0;
   out_5691168246274914733[44] = 1;
   out_5691168246274914733[45] = 0;
   out_5691168246274914733[46] = 0;
   out_5691168246274914733[47] = 1;
   out_5691168246274914733[48] = 0;
   out_5691168246274914733[49] = 0;
   out_5691168246274914733[50] = 0;
   out_5691168246274914733[51] = 0;
   out_5691168246274914733[52] = 0;
   out_5691168246274914733[53] = 0;
}
void h_10(double *state, double *unused, double *out_6728942981811315921) {
   out_6728942981811315921[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_6728942981811315921[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_6728942981811315921[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_4278506402956144046) {
   out_4278506402956144046[0] = 0;
   out_4278506402956144046[1] = 9.8100000000000005*cos(state[1]);
   out_4278506402956144046[2] = 0;
   out_4278506402956144046[3] = 0;
   out_4278506402956144046[4] = -state[8];
   out_4278506402956144046[5] = state[7];
   out_4278506402956144046[6] = 0;
   out_4278506402956144046[7] = state[5];
   out_4278506402956144046[8] = -state[4];
   out_4278506402956144046[9] = 0;
   out_4278506402956144046[10] = 0;
   out_4278506402956144046[11] = 0;
   out_4278506402956144046[12] = 1;
   out_4278506402956144046[13] = 0;
   out_4278506402956144046[14] = 0;
   out_4278506402956144046[15] = 1;
   out_4278506402956144046[16] = 0;
   out_4278506402956144046[17] = 0;
   out_4278506402956144046[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_4278506402956144046[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_4278506402956144046[20] = 0;
   out_4278506402956144046[21] = state[8];
   out_4278506402956144046[22] = 0;
   out_4278506402956144046[23] = -state[6];
   out_4278506402956144046[24] = -state[5];
   out_4278506402956144046[25] = 0;
   out_4278506402956144046[26] = state[3];
   out_4278506402956144046[27] = 0;
   out_4278506402956144046[28] = 0;
   out_4278506402956144046[29] = 0;
   out_4278506402956144046[30] = 0;
   out_4278506402956144046[31] = 1;
   out_4278506402956144046[32] = 0;
   out_4278506402956144046[33] = 0;
   out_4278506402956144046[34] = 1;
   out_4278506402956144046[35] = 0;
   out_4278506402956144046[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_4278506402956144046[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_4278506402956144046[38] = 0;
   out_4278506402956144046[39] = -state[7];
   out_4278506402956144046[40] = state[6];
   out_4278506402956144046[41] = 0;
   out_4278506402956144046[42] = state[4];
   out_4278506402956144046[43] = -state[3];
   out_4278506402956144046[44] = 0;
   out_4278506402956144046[45] = 0;
   out_4278506402956144046[46] = 0;
   out_4278506402956144046[47] = 0;
   out_4278506402956144046[48] = 0;
   out_4278506402956144046[49] = 0;
   out_4278506402956144046[50] = 1;
   out_4278506402956144046[51] = 0;
   out_4278506402956144046[52] = 0;
   out_4278506402956144046[53] = 1;
}
void h_13(double *state, double *unused, double *out_1205451540469147746) {
   out_1205451540469147746[0] = state[3];
   out_1205451540469147746[1] = state[4];
   out_1205451540469147746[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8903442071607247534) {
   out_8903442071607247534[0] = 0;
   out_8903442071607247534[1] = 0;
   out_8903442071607247534[2] = 0;
   out_8903442071607247534[3] = 1;
   out_8903442071607247534[4] = 0;
   out_8903442071607247534[5] = 0;
   out_8903442071607247534[6] = 0;
   out_8903442071607247534[7] = 0;
   out_8903442071607247534[8] = 0;
   out_8903442071607247534[9] = 0;
   out_8903442071607247534[10] = 0;
   out_8903442071607247534[11] = 0;
   out_8903442071607247534[12] = 0;
   out_8903442071607247534[13] = 0;
   out_8903442071607247534[14] = 0;
   out_8903442071607247534[15] = 0;
   out_8903442071607247534[16] = 0;
   out_8903442071607247534[17] = 0;
   out_8903442071607247534[18] = 0;
   out_8903442071607247534[19] = 0;
   out_8903442071607247534[20] = 0;
   out_8903442071607247534[21] = 0;
   out_8903442071607247534[22] = 1;
   out_8903442071607247534[23] = 0;
   out_8903442071607247534[24] = 0;
   out_8903442071607247534[25] = 0;
   out_8903442071607247534[26] = 0;
   out_8903442071607247534[27] = 0;
   out_8903442071607247534[28] = 0;
   out_8903442071607247534[29] = 0;
   out_8903442071607247534[30] = 0;
   out_8903442071607247534[31] = 0;
   out_8903442071607247534[32] = 0;
   out_8903442071607247534[33] = 0;
   out_8903442071607247534[34] = 0;
   out_8903442071607247534[35] = 0;
   out_8903442071607247534[36] = 0;
   out_8903442071607247534[37] = 0;
   out_8903442071607247534[38] = 0;
   out_8903442071607247534[39] = 0;
   out_8903442071607247534[40] = 0;
   out_8903442071607247534[41] = 1;
   out_8903442071607247534[42] = 0;
   out_8903442071607247534[43] = 0;
   out_8903442071607247534[44] = 0;
   out_8903442071607247534[45] = 0;
   out_8903442071607247534[46] = 0;
   out_8903442071607247534[47] = 0;
   out_8903442071607247534[48] = 0;
   out_8903442071607247534[49] = 0;
   out_8903442071607247534[50] = 0;
   out_8903442071607247534[51] = 0;
   out_8903442071607247534[52] = 0;
   out_8903442071607247534[53] = 0;
}
void h_14(double *state, double *unused, double *out_3303339494882182614) {
   out_3303339494882182614[0] = state[6];
   out_3303339494882182614[1] = state[7];
   out_3303339494882182614[2] = state[8];
}
void H_14(double *state, double *unused, double *out_8792334971095152354) {
   out_8792334971095152354[0] = 0;
   out_8792334971095152354[1] = 0;
   out_8792334971095152354[2] = 0;
   out_8792334971095152354[3] = 0;
   out_8792334971095152354[4] = 0;
   out_8792334971095152354[5] = 0;
   out_8792334971095152354[6] = 1;
   out_8792334971095152354[7] = 0;
   out_8792334971095152354[8] = 0;
   out_8792334971095152354[9] = 0;
   out_8792334971095152354[10] = 0;
   out_8792334971095152354[11] = 0;
   out_8792334971095152354[12] = 0;
   out_8792334971095152354[13] = 0;
   out_8792334971095152354[14] = 0;
   out_8792334971095152354[15] = 0;
   out_8792334971095152354[16] = 0;
   out_8792334971095152354[17] = 0;
   out_8792334971095152354[18] = 0;
   out_8792334971095152354[19] = 0;
   out_8792334971095152354[20] = 0;
   out_8792334971095152354[21] = 0;
   out_8792334971095152354[22] = 0;
   out_8792334971095152354[23] = 0;
   out_8792334971095152354[24] = 0;
   out_8792334971095152354[25] = 1;
   out_8792334971095152354[26] = 0;
   out_8792334971095152354[27] = 0;
   out_8792334971095152354[28] = 0;
   out_8792334971095152354[29] = 0;
   out_8792334971095152354[30] = 0;
   out_8792334971095152354[31] = 0;
   out_8792334971095152354[32] = 0;
   out_8792334971095152354[33] = 0;
   out_8792334971095152354[34] = 0;
   out_8792334971095152354[35] = 0;
   out_8792334971095152354[36] = 0;
   out_8792334971095152354[37] = 0;
   out_8792334971095152354[38] = 0;
   out_8792334971095152354[39] = 0;
   out_8792334971095152354[40] = 0;
   out_8792334971095152354[41] = 0;
   out_8792334971095152354[42] = 0;
   out_8792334971095152354[43] = 0;
   out_8792334971095152354[44] = 1;
   out_8792334971095152354[45] = 0;
   out_8792334971095152354[46] = 0;
   out_8792334971095152354[47] = 0;
   out_8792334971095152354[48] = 0;
   out_8792334971095152354[49] = 0;
   out_8792334971095152354[50] = 0;
   out_8792334971095152354[51] = 0;
   out_8792334971095152354[52] = 0;
   out_8792334971095152354[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_4967863734907407968) {
  err_fun(nom_x, delta_x, out_4967863734907407968);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_554301816764323460) {
  inv_err_fun(nom_x, true_x, out_554301816764323460);
}
void pose_H_mod_fun(double *state, double *out_3047027985808074405) {
  H_mod_fun(state, out_3047027985808074405);
}
void pose_f_fun(double *state, double dt, double *out_986492010673501731) {
  f_fun(state,  dt, out_986492010673501731);
}
void pose_F_fun(double *state, double dt, double *out_4336070434649428420) {
  F_fun(state,  dt, out_4336070434649428420);
}
void pose_h_4(double *state, double *unused, double *out_5526642384709914880) {
  h_4(state, unused, out_5526642384709914880);
}
void pose_H_4(double *state, double *unused, double *out_5691168246274914733) {
  H_4(state, unused, out_5691168246274914733);
}
void pose_h_10(double *state, double *unused, double *out_6728942981811315921) {
  h_10(state, unused, out_6728942981811315921);
}
void pose_H_10(double *state, double *unused, double *out_4278506402956144046) {
  H_10(state, unused, out_4278506402956144046);
}
void pose_h_13(double *state, double *unused, double *out_1205451540469147746) {
  h_13(state, unused, out_1205451540469147746);
}
void pose_H_13(double *state, double *unused, double *out_8903442071607247534) {
  H_13(state, unused, out_8903442071607247534);
}
void pose_h_14(double *state, double *unused, double *out_3303339494882182614) {
  h_14(state, unused, out_3303339494882182614);
}
void pose_H_14(double *state, double *unused, double *out_8792334971095152354) {
  H_14(state, unused, out_8792334971095152354);
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
