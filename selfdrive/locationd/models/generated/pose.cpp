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
void err_fun(double *nom_x, double *delta_x, double *out_494363428253979517) {
   out_494363428253979517[0] = delta_x[0] + nom_x[0];
   out_494363428253979517[1] = delta_x[1] + nom_x[1];
   out_494363428253979517[2] = delta_x[2] + nom_x[2];
   out_494363428253979517[3] = delta_x[3] + nom_x[3];
   out_494363428253979517[4] = delta_x[4] + nom_x[4];
   out_494363428253979517[5] = delta_x[5] + nom_x[5];
   out_494363428253979517[6] = delta_x[6] + nom_x[6];
   out_494363428253979517[7] = delta_x[7] + nom_x[7];
   out_494363428253979517[8] = delta_x[8] + nom_x[8];
   out_494363428253979517[9] = delta_x[9] + nom_x[9];
   out_494363428253979517[10] = delta_x[10] + nom_x[10];
   out_494363428253979517[11] = delta_x[11] + nom_x[11];
   out_494363428253979517[12] = delta_x[12] + nom_x[12];
   out_494363428253979517[13] = delta_x[13] + nom_x[13];
   out_494363428253979517[14] = delta_x[14] + nom_x[14];
   out_494363428253979517[15] = delta_x[15] + nom_x[15];
   out_494363428253979517[16] = delta_x[16] + nom_x[16];
   out_494363428253979517[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7744180703950466915) {
   out_7744180703950466915[0] = -nom_x[0] + true_x[0];
   out_7744180703950466915[1] = -nom_x[1] + true_x[1];
   out_7744180703950466915[2] = -nom_x[2] + true_x[2];
   out_7744180703950466915[3] = -nom_x[3] + true_x[3];
   out_7744180703950466915[4] = -nom_x[4] + true_x[4];
   out_7744180703950466915[5] = -nom_x[5] + true_x[5];
   out_7744180703950466915[6] = -nom_x[6] + true_x[6];
   out_7744180703950466915[7] = -nom_x[7] + true_x[7];
   out_7744180703950466915[8] = -nom_x[8] + true_x[8];
   out_7744180703950466915[9] = -nom_x[9] + true_x[9];
   out_7744180703950466915[10] = -nom_x[10] + true_x[10];
   out_7744180703950466915[11] = -nom_x[11] + true_x[11];
   out_7744180703950466915[12] = -nom_x[12] + true_x[12];
   out_7744180703950466915[13] = -nom_x[13] + true_x[13];
   out_7744180703950466915[14] = -nom_x[14] + true_x[14];
   out_7744180703950466915[15] = -nom_x[15] + true_x[15];
   out_7744180703950466915[16] = -nom_x[16] + true_x[16];
   out_7744180703950466915[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_8790605035544908227) {
   out_8790605035544908227[0] = 1.0;
   out_8790605035544908227[1] = 0.0;
   out_8790605035544908227[2] = 0.0;
   out_8790605035544908227[3] = 0.0;
   out_8790605035544908227[4] = 0.0;
   out_8790605035544908227[5] = 0.0;
   out_8790605035544908227[6] = 0.0;
   out_8790605035544908227[7] = 0.0;
   out_8790605035544908227[8] = 0.0;
   out_8790605035544908227[9] = 0.0;
   out_8790605035544908227[10] = 0.0;
   out_8790605035544908227[11] = 0.0;
   out_8790605035544908227[12] = 0.0;
   out_8790605035544908227[13] = 0.0;
   out_8790605035544908227[14] = 0.0;
   out_8790605035544908227[15] = 0.0;
   out_8790605035544908227[16] = 0.0;
   out_8790605035544908227[17] = 0.0;
   out_8790605035544908227[18] = 0.0;
   out_8790605035544908227[19] = 1.0;
   out_8790605035544908227[20] = 0.0;
   out_8790605035544908227[21] = 0.0;
   out_8790605035544908227[22] = 0.0;
   out_8790605035544908227[23] = 0.0;
   out_8790605035544908227[24] = 0.0;
   out_8790605035544908227[25] = 0.0;
   out_8790605035544908227[26] = 0.0;
   out_8790605035544908227[27] = 0.0;
   out_8790605035544908227[28] = 0.0;
   out_8790605035544908227[29] = 0.0;
   out_8790605035544908227[30] = 0.0;
   out_8790605035544908227[31] = 0.0;
   out_8790605035544908227[32] = 0.0;
   out_8790605035544908227[33] = 0.0;
   out_8790605035544908227[34] = 0.0;
   out_8790605035544908227[35] = 0.0;
   out_8790605035544908227[36] = 0.0;
   out_8790605035544908227[37] = 0.0;
   out_8790605035544908227[38] = 1.0;
   out_8790605035544908227[39] = 0.0;
   out_8790605035544908227[40] = 0.0;
   out_8790605035544908227[41] = 0.0;
   out_8790605035544908227[42] = 0.0;
   out_8790605035544908227[43] = 0.0;
   out_8790605035544908227[44] = 0.0;
   out_8790605035544908227[45] = 0.0;
   out_8790605035544908227[46] = 0.0;
   out_8790605035544908227[47] = 0.0;
   out_8790605035544908227[48] = 0.0;
   out_8790605035544908227[49] = 0.0;
   out_8790605035544908227[50] = 0.0;
   out_8790605035544908227[51] = 0.0;
   out_8790605035544908227[52] = 0.0;
   out_8790605035544908227[53] = 0.0;
   out_8790605035544908227[54] = 0.0;
   out_8790605035544908227[55] = 0.0;
   out_8790605035544908227[56] = 0.0;
   out_8790605035544908227[57] = 1.0;
   out_8790605035544908227[58] = 0.0;
   out_8790605035544908227[59] = 0.0;
   out_8790605035544908227[60] = 0.0;
   out_8790605035544908227[61] = 0.0;
   out_8790605035544908227[62] = 0.0;
   out_8790605035544908227[63] = 0.0;
   out_8790605035544908227[64] = 0.0;
   out_8790605035544908227[65] = 0.0;
   out_8790605035544908227[66] = 0.0;
   out_8790605035544908227[67] = 0.0;
   out_8790605035544908227[68] = 0.0;
   out_8790605035544908227[69] = 0.0;
   out_8790605035544908227[70] = 0.0;
   out_8790605035544908227[71] = 0.0;
   out_8790605035544908227[72] = 0.0;
   out_8790605035544908227[73] = 0.0;
   out_8790605035544908227[74] = 0.0;
   out_8790605035544908227[75] = 0.0;
   out_8790605035544908227[76] = 1.0;
   out_8790605035544908227[77] = 0.0;
   out_8790605035544908227[78] = 0.0;
   out_8790605035544908227[79] = 0.0;
   out_8790605035544908227[80] = 0.0;
   out_8790605035544908227[81] = 0.0;
   out_8790605035544908227[82] = 0.0;
   out_8790605035544908227[83] = 0.0;
   out_8790605035544908227[84] = 0.0;
   out_8790605035544908227[85] = 0.0;
   out_8790605035544908227[86] = 0.0;
   out_8790605035544908227[87] = 0.0;
   out_8790605035544908227[88] = 0.0;
   out_8790605035544908227[89] = 0.0;
   out_8790605035544908227[90] = 0.0;
   out_8790605035544908227[91] = 0.0;
   out_8790605035544908227[92] = 0.0;
   out_8790605035544908227[93] = 0.0;
   out_8790605035544908227[94] = 0.0;
   out_8790605035544908227[95] = 1.0;
   out_8790605035544908227[96] = 0.0;
   out_8790605035544908227[97] = 0.0;
   out_8790605035544908227[98] = 0.0;
   out_8790605035544908227[99] = 0.0;
   out_8790605035544908227[100] = 0.0;
   out_8790605035544908227[101] = 0.0;
   out_8790605035544908227[102] = 0.0;
   out_8790605035544908227[103] = 0.0;
   out_8790605035544908227[104] = 0.0;
   out_8790605035544908227[105] = 0.0;
   out_8790605035544908227[106] = 0.0;
   out_8790605035544908227[107] = 0.0;
   out_8790605035544908227[108] = 0.0;
   out_8790605035544908227[109] = 0.0;
   out_8790605035544908227[110] = 0.0;
   out_8790605035544908227[111] = 0.0;
   out_8790605035544908227[112] = 0.0;
   out_8790605035544908227[113] = 0.0;
   out_8790605035544908227[114] = 1.0;
   out_8790605035544908227[115] = 0.0;
   out_8790605035544908227[116] = 0.0;
   out_8790605035544908227[117] = 0.0;
   out_8790605035544908227[118] = 0.0;
   out_8790605035544908227[119] = 0.0;
   out_8790605035544908227[120] = 0.0;
   out_8790605035544908227[121] = 0.0;
   out_8790605035544908227[122] = 0.0;
   out_8790605035544908227[123] = 0.0;
   out_8790605035544908227[124] = 0.0;
   out_8790605035544908227[125] = 0.0;
   out_8790605035544908227[126] = 0.0;
   out_8790605035544908227[127] = 0.0;
   out_8790605035544908227[128] = 0.0;
   out_8790605035544908227[129] = 0.0;
   out_8790605035544908227[130] = 0.0;
   out_8790605035544908227[131] = 0.0;
   out_8790605035544908227[132] = 0.0;
   out_8790605035544908227[133] = 1.0;
   out_8790605035544908227[134] = 0.0;
   out_8790605035544908227[135] = 0.0;
   out_8790605035544908227[136] = 0.0;
   out_8790605035544908227[137] = 0.0;
   out_8790605035544908227[138] = 0.0;
   out_8790605035544908227[139] = 0.0;
   out_8790605035544908227[140] = 0.0;
   out_8790605035544908227[141] = 0.0;
   out_8790605035544908227[142] = 0.0;
   out_8790605035544908227[143] = 0.0;
   out_8790605035544908227[144] = 0.0;
   out_8790605035544908227[145] = 0.0;
   out_8790605035544908227[146] = 0.0;
   out_8790605035544908227[147] = 0.0;
   out_8790605035544908227[148] = 0.0;
   out_8790605035544908227[149] = 0.0;
   out_8790605035544908227[150] = 0.0;
   out_8790605035544908227[151] = 0.0;
   out_8790605035544908227[152] = 1.0;
   out_8790605035544908227[153] = 0.0;
   out_8790605035544908227[154] = 0.0;
   out_8790605035544908227[155] = 0.0;
   out_8790605035544908227[156] = 0.0;
   out_8790605035544908227[157] = 0.0;
   out_8790605035544908227[158] = 0.0;
   out_8790605035544908227[159] = 0.0;
   out_8790605035544908227[160] = 0.0;
   out_8790605035544908227[161] = 0.0;
   out_8790605035544908227[162] = 0.0;
   out_8790605035544908227[163] = 0.0;
   out_8790605035544908227[164] = 0.0;
   out_8790605035544908227[165] = 0.0;
   out_8790605035544908227[166] = 0.0;
   out_8790605035544908227[167] = 0.0;
   out_8790605035544908227[168] = 0.0;
   out_8790605035544908227[169] = 0.0;
   out_8790605035544908227[170] = 0.0;
   out_8790605035544908227[171] = 1.0;
   out_8790605035544908227[172] = 0.0;
   out_8790605035544908227[173] = 0.0;
   out_8790605035544908227[174] = 0.0;
   out_8790605035544908227[175] = 0.0;
   out_8790605035544908227[176] = 0.0;
   out_8790605035544908227[177] = 0.0;
   out_8790605035544908227[178] = 0.0;
   out_8790605035544908227[179] = 0.0;
   out_8790605035544908227[180] = 0.0;
   out_8790605035544908227[181] = 0.0;
   out_8790605035544908227[182] = 0.0;
   out_8790605035544908227[183] = 0.0;
   out_8790605035544908227[184] = 0.0;
   out_8790605035544908227[185] = 0.0;
   out_8790605035544908227[186] = 0.0;
   out_8790605035544908227[187] = 0.0;
   out_8790605035544908227[188] = 0.0;
   out_8790605035544908227[189] = 0.0;
   out_8790605035544908227[190] = 1.0;
   out_8790605035544908227[191] = 0.0;
   out_8790605035544908227[192] = 0.0;
   out_8790605035544908227[193] = 0.0;
   out_8790605035544908227[194] = 0.0;
   out_8790605035544908227[195] = 0.0;
   out_8790605035544908227[196] = 0.0;
   out_8790605035544908227[197] = 0.0;
   out_8790605035544908227[198] = 0.0;
   out_8790605035544908227[199] = 0.0;
   out_8790605035544908227[200] = 0.0;
   out_8790605035544908227[201] = 0.0;
   out_8790605035544908227[202] = 0.0;
   out_8790605035544908227[203] = 0.0;
   out_8790605035544908227[204] = 0.0;
   out_8790605035544908227[205] = 0.0;
   out_8790605035544908227[206] = 0.0;
   out_8790605035544908227[207] = 0.0;
   out_8790605035544908227[208] = 0.0;
   out_8790605035544908227[209] = 1.0;
   out_8790605035544908227[210] = 0.0;
   out_8790605035544908227[211] = 0.0;
   out_8790605035544908227[212] = 0.0;
   out_8790605035544908227[213] = 0.0;
   out_8790605035544908227[214] = 0.0;
   out_8790605035544908227[215] = 0.0;
   out_8790605035544908227[216] = 0.0;
   out_8790605035544908227[217] = 0.0;
   out_8790605035544908227[218] = 0.0;
   out_8790605035544908227[219] = 0.0;
   out_8790605035544908227[220] = 0.0;
   out_8790605035544908227[221] = 0.0;
   out_8790605035544908227[222] = 0.0;
   out_8790605035544908227[223] = 0.0;
   out_8790605035544908227[224] = 0.0;
   out_8790605035544908227[225] = 0.0;
   out_8790605035544908227[226] = 0.0;
   out_8790605035544908227[227] = 0.0;
   out_8790605035544908227[228] = 1.0;
   out_8790605035544908227[229] = 0.0;
   out_8790605035544908227[230] = 0.0;
   out_8790605035544908227[231] = 0.0;
   out_8790605035544908227[232] = 0.0;
   out_8790605035544908227[233] = 0.0;
   out_8790605035544908227[234] = 0.0;
   out_8790605035544908227[235] = 0.0;
   out_8790605035544908227[236] = 0.0;
   out_8790605035544908227[237] = 0.0;
   out_8790605035544908227[238] = 0.0;
   out_8790605035544908227[239] = 0.0;
   out_8790605035544908227[240] = 0.0;
   out_8790605035544908227[241] = 0.0;
   out_8790605035544908227[242] = 0.0;
   out_8790605035544908227[243] = 0.0;
   out_8790605035544908227[244] = 0.0;
   out_8790605035544908227[245] = 0.0;
   out_8790605035544908227[246] = 0.0;
   out_8790605035544908227[247] = 1.0;
   out_8790605035544908227[248] = 0.0;
   out_8790605035544908227[249] = 0.0;
   out_8790605035544908227[250] = 0.0;
   out_8790605035544908227[251] = 0.0;
   out_8790605035544908227[252] = 0.0;
   out_8790605035544908227[253] = 0.0;
   out_8790605035544908227[254] = 0.0;
   out_8790605035544908227[255] = 0.0;
   out_8790605035544908227[256] = 0.0;
   out_8790605035544908227[257] = 0.0;
   out_8790605035544908227[258] = 0.0;
   out_8790605035544908227[259] = 0.0;
   out_8790605035544908227[260] = 0.0;
   out_8790605035544908227[261] = 0.0;
   out_8790605035544908227[262] = 0.0;
   out_8790605035544908227[263] = 0.0;
   out_8790605035544908227[264] = 0.0;
   out_8790605035544908227[265] = 0.0;
   out_8790605035544908227[266] = 1.0;
   out_8790605035544908227[267] = 0.0;
   out_8790605035544908227[268] = 0.0;
   out_8790605035544908227[269] = 0.0;
   out_8790605035544908227[270] = 0.0;
   out_8790605035544908227[271] = 0.0;
   out_8790605035544908227[272] = 0.0;
   out_8790605035544908227[273] = 0.0;
   out_8790605035544908227[274] = 0.0;
   out_8790605035544908227[275] = 0.0;
   out_8790605035544908227[276] = 0.0;
   out_8790605035544908227[277] = 0.0;
   out_8790605035544908227[278] = 0.0;
   out_8790605035544908227[279] = 0.0;
   out_8790605035544908227[280] = 0.0;
   out_8790605035544908227[281] = 0.0;
   out_8790605035544908227[282] = 0.0;
   out_8790605035544908227[283] = 0.0;
   out_8790605035544908227[284] = 0.0;
   out_8790605035544908227[285] = 1.0;
   out_8790605035544908227[286] = 0.0;
   out_8790605035544908227[287] = 0.0;
   out_8790605035544908227[288] = 0.0;
   out_8790605035544908227[289] = 0.0;
   out_8790605035544908227[290] = 0.0;
   out_8790605035544908227[291] = 0.0;
   out_8790605035544908227[292] = 0.0;
   out_8790605035544908227[293] = 0.0;
   out_8790605035544908227[294] = 0.0;
   out_8790605035544908227[295] = 0.0;
   out_8790605035544908227[296] = 0.0;
   out_8790605035544908227[297] = 0.0;
   out_8790605035544908227[298] = 0.0;
   out_8790605035544908227[299] = 0.0;
   out_8790605035544908227[300] = 0.0;
   out_8790605035544908227[301] = 0.0;
   out_8790605035544908227[302] = 0.0;
   out_8790605035544908227[303] = 0.0;
   out_8790605035544908227[304] = 1.0;
   out_8790605035544908227[305] = 0.0;
   out_8790605035544908227[306] = 0.0;
   out_8790605035544908227[307] = 0.0;
   out_8790605035544908227[308] = 0.0;
   out_8790605035544908227[309] = 0.0;
   out_8790605035544908227[310] = 0.0;
   out_8790605035544908227[311] = 0.0;
   out_8790605035544908227[312] = 0.0;
   out_8790605035544908227[313] = 0.0;
   out_8790605035544908227[314] = 0.0;
   out_8790605035544908227[315] = 0.0;
   out_8790605035544908227[316] = 0.0;
   out_8790605035544908227[317] = 0.0;
   out_8790605035544908227[318] = 0.0;
   out_8790605035544908227[319] = 0.0;
   out_8790605035544908227[320] = 0.0;
   out_8790605035544908227[321] = 0.0;
   out_8790605035544908227[322] = 0.0;
   out_8790605035544908227[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4191169391561892498) {
   out_4191169391561892498[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4191169391561892498[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4191169391561892498[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4191169391561892498[3] = dt*state[12] + state[3];
   out_4191169391561892498[4] = dt*state[13] + state[4];
   out_4191169391561892498[5] = dt*state[14] + state[5];
   out_4191169391561892498[6] = state[6];
   out_4191169391561892498[7] = state[7];
   out_4191169391561892498[8] = state[8];
   out_4191169391561892498[9] = state[9];
   out_4191169391561892498[10] = state[10];
   out_4191169391561892498[11] = state[11];
   out_4191169391561892498[12] = state[12];
   out_4191169391561892498[13] = state[13];
   out_4191169391561892498[14] = state[14];
   out_4191169391561892498[15] = state[15];
   out_4191169391561892498[16] = state[16];
   out_4191169391561892498[17] = state[17];
}
void F_fun(double *state, double dt, double *out_7295826236279740984) {
   out_7295826236279740984[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7295826236279740984[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7295826236279740984[2] = 0;
   out_7295826236279740984[3] = 0;
   out_7295826236279740984[4] = 0;
   out_7295826236279740984[5] = 0;
   out_7295826236279740984[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7295826236279740984[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7295826236279740984[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7295826236279740984[9] = 0;
   out_7295826236279740984[10] = 0;
   out_7295826236279740984[11] = 0;
   out_7295826236279740984[12] = 0;
   out_7295826236279740984[13] = 0;
   out_7295826236279740984[14] = 0;
   out_7295826236279740984[15] = 0;
   out_7295826236279740984[16] = 0;
   out_7295826236279740984[17] = 0;
   out_7295826236279740984[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7295826236279740984[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7295826236279740984[20] = 0;
   out_7295826236279740984[21] = 0;
   out_7295826236279740984[22] = 0;
   out_7295826236279740984[23] = 0;
   out_7295826236279740984[24] = 0;
   out_7295826236279740984[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7295826236279740984[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7295826236279740984[27] = 0;
   out_7295826236279740984[28] = 0;
   out_7295826236279740984[29] = 0;
   out_7295826236279740984[30] = 0;
   out_7295826236279740984[31] = 0;
   out_7295826236279740984[32] = 0;
   out_7295826236279740984[33] = 0;
   out_7295826236279740984[34] = 0;
   out_7295826236279740984[35] = 0;
   out_7295826236279740984[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7295826236279740984[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7295826236279740984[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7295826236279740984[39] = 0;
   out_7295826236279740984[40] = 0;
   out_7295826236279740984[41] = 0;
   out_7295826236279740984[42] = 0;
   out_7295826236279740984[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7295826236279740984[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7295826236279740984[45] = 0;
   out_7295826236279740984[46] = 0;
   out_7295826236279740984[47] = 0;
   out_7295826236279740984[48] = 0;
   out_7295826236279740984[49] = 0;
   out_7295826236279740984[50] = 0;
   out_7295826236279740984[51] = 0;
   out_7295826236279740984[52] = 0;
   out_7295826236279740984[53] = 0;
   out_7295826236279740984[54] = 0;
   out_7295826236279740984[55] = 0;
   out_7295826236279740984[56] = 0;
   out_7295826236279740984[57] = 1;
   out_7295826236279740984[58] = 0;
   out_7295826236279740984[59] = 0;
   out_7295826236279740984[60] = 0;
   out_7295826236279740984[61] = 0;
   out_7295826236279740984[62] = 0;
   out_7295826236279740984[63] = 0;
   out_7295826236279740984[64] = 0;
   out_7295826236279740984[65] = 0;
   out_7295826236279740984[66] = dt;
   out_7295826236279740984[67] = 0;
   out_7295826236279740984[68] = 0;
   out_7295826236279740984[69] = 0;
   out_7295826236279740984[70] = 0;
   out_7295826236279740984[71] = 0;
   out_7295826236279740984[72] = 0;
   out_7295826236279740984[73] = 0;
   out_7295826236279740984[74] = 0;
   out_7295826236279740984[75] = 0;
   out_7295826236279740984[76] = 1;
   out_7295826236279740984[77] = 0;
   out_7295826236279740984[78] = 0;
   out_7295826236279740984[79] = 0;
   out_7295826236279740984[80] = 0;
   out_7295826236279740984[81] = 0;
   out_7295826236279740984[82] = 0;
   out_7295826236279740984[83] = 0;
   out_7295826236279740984[84] = 0;
   out_7295826236279740984[85] = dt;
   out_7295826236279740984[86] = 0;
   out_7295826236279740984[87] = 0;
   out_7295826236279740984[88] = 0;
   out_7295826236279740984[89] = 0;
   out_7295826236279740984[90] = 0;
   out_7295826236279740984[91] = 0;
   out_7295826236279740984[92] = 0;
   out_7295826236279740984[93] = 0;
   out_7295826236279740984[94] = 0;
   out_7295826236279740984[95] = 1;
   out_7295826236279740984[96] = 0;
   out_7295826236279740984[97] = 0;
   out_7295826236279740984[98] = 0;
   out_7295826236279740984[99] = 0;
   out_7295826236279740984[100] = 0;
   out_7295826236279740984[101] = 0;
   out_7295826236279740984[102] = 0;
   out_7295826236279740984[103] = 0;
   out_7295826236279740984[104] = dt;
   out_7295826236279740984[105] = 0;
   out_7295826236279740984[106] = 0;
   out_7295826236279740984[107] = 0;
   out_7295826236279740984[108] = 0;
   out_7295826236279740984[109] = 0;
   out_7295826236279740984[110] = 0;
   out_7295826236279740984[111] = 0;
   out_7295826236279740984[112] = 0;
   out_7295826236279740984[113] = 0;
   out_7295826236279740984[114] = 1;
   out_7295826236279740984[115] = 0;
   out_7295826236279740984[116] = 0;
   out_7295826236279740984[117] = 0;
   out_7295826236279740984[118] = 0;
   out_7295826236279740984[119] = 0;
   out_7295826236279740984[120] = 0;
   out_7295826236279740984[121] = 0;
   out_7295826236279740984[122] = 0;
   out_7295826236279740984[123] = 0;
   out_7295826236279740984[124] = 0;
   out_7295826236279740984[125] = 0;
   out_7295826236279740984[126] = 0;
   out_7295826236279740984[127] = 0;
   out_7295826236279740984[128] = 0;
   out_7295826236279740984[129] = 0;
   out_7295826236279740984[130] = 0;
   out_7295826236279740984[131] = 0;
   out_7295826236279740984[132] = 0;
   out_7295826236279740984[133] = 1;
   out_7295826236279740984[134] = 0;
   out_7295826236279740984[135] = 0;
   out_7295826236279740984[136] = 0;
   out_7295826236279740984[137] = 0;
   out_7295826236279740984[138] = 0;
   out_7295826236279740984[139] = 0;
   out_7295826236279740984[140] = 0;
   out_7295826236279740984[141] = 0;
   out_7295826236279740984[142] = 0;
   out_7295826236279740984[143] = 0;
   out_7295826236279740984[144] = 0;
   out_7295826236279740984[145] = 0;
   out_7295826236279740984[146] = 0;
   out_7295826236279740984[147] = 0;
   out_7295826236279740984[148] = 0;
   out_7295826236279740984[149] = 0;
   out_7295826236279740984[150] = 0;
   out_7295826236279740984[151] = 0;
   out_7295826236279740984[152] = 1;
   out_7295826236279740984[153] = 0;
   out_7295826236279740984[154] = 0;
   out_7295826236279740984[155] = 0;
   out_7295826236279740984[156] = 0;
   out_7295826236279740984[157] = 0;
   out_7295826236279740984[158] = 0;
   out_7295826236279740984[159] = 0;
   out_7295826236279740984[160] = 0;
   out_7295826236279740984[161] = 0;
   out_7295826236279740984[162] = 0;
   out_7295826236279740984[163] = 0;
   out_7295826236279740984[164] = 0;
   out_7295826236279740984[165] = 0;
   out_7295826236279740984[166] = 0;
   out_7295826236279740984[167] = 0;
   out_7295826236279740984[168] = 0;
   out_7295826236279740984[169] = 0;
   out_7295826236279740984[170] = 0;
   out_7295826236279740984[171] = 1;
   out_7295826236279740984[172] = 0;
   out_7295826236279740984[173] = 0;
   out_7295826236279740984[174] = 0;
   out_7295826236279740984[175] = 0;
   out_7295826236279740984[176] = 0;
   out_7295826236279740984[177] = 0;
   out_7295826236279740984[178] = 0;
   out_7295826236279740984[179] = 0;
   out_7295826236279740984[180] = 0;
   out_7295826236279740984[181] = 0;
   out_7295826236279740984[182] = 0;
   out_7295826236279740984[183] = 0;
   out_7295826236279740984[184] = 0;
   out_7295826236279740984[185] = 0;
   out_7295826236279740984[186] = 0;
   out_7295826236279740984[187] = 0;
   out_7295826236279740984[188] = 0;
   out_7295826236279740984[189] = 0;
   out_7295826236279740984[190] = 1;
   out_7295826236279740984[191] = 0;
   out_7295826236279740984[192] = 0;
   out_7295826236279740984[193] = 0;
   out_7295826236279740984[194] = 0;
   out_7295826236279740984[195] = 0;
   out_7295826236279740984[196] = 0;
   out_7295826236279740984[197] = 0;
   out_7295826236279740984[198] = 0;
   out_7295826236279740984[199] = 0;
   out_7295826236279740984[200] = 0;
   out_7295826236279740984[201] = 0;
   out_7295826236279740984[202] = 0;
   out_7295826236279740984[203] = 0;
   out_7295826236279740984[204] = 0;
   out_7295826236279740984[205] = 0;
   out_7295826236279740984[206] = 0;
   out_7295826236279740984[207] = 0;
   out_7295826236279740984[208] = 0;
   out_7295826236279740984[209] = 1;
   out_7295826236279740984[210] = 0;
   out_7295826236279740984[211] = 0;
   out_7295826236279740984[212] = 0;
   out_7295826236279740984[213] = 0;
   out_7295826236279740984[214] = 0;
   out_7295826236279740984[215] = 0;
   out_7295826236279740984[216] = 0;
   out_7295826236279740984[217] = 0;
   out_7295826236279740984[218] = 0;
   out_7295826236279740984[219] = 0;
   out_7295826236279740984[220] = 0;
   out_7295826236279740984[221] = 0;
   out_7295826236279740984[222] = 0;
   out_7295826236279740984[223] = 0;
   out_7295826236279740984[224] = 0;
   out_7295826236279740984[225] = 0;
   out_7295826236279740984[226] = 0;
   out_7295826236279740984[227] = 0;
   out_7295826236279740984[228] = 1;
   out_7295826236279740984[229] = 0;
   out_7295826236279740984[230] = 0;
   out_7295826236279740984[231] = 0;
   out_7295826236279740984[232] = 0;
   out_7295826236279740984[233] = 0;
   out_7295826236279740984[234] = 0;
   out_7295826236279740984[235] = 0;
   out_7295826236279740984[236] = 0;
   out_7295826236279740984[237] = 0;
   out_7295826236279740984[238] = 0;
   out_7295826236279740984[239] = 0;
   out_7295826236279740984[240] = 0;
   out_7295826236279740984[241] = 0;
   out_7295826236279740984[242] = 0;
   out_7295826236279740984[243] = 0;
   out_7295826236279740984[244] = 0;
   out_7295826236279740984[245] = 0;
   out_7295826236279740984[246] = 0;
   out_7295826236279740984[247] = 1;
   out_7295826236279740984[248] = 0;
   out_7295826236279740984[249] = 0;
   out_7295826236279740984[250] = 0;
   out_7295826236279740984[251] = 0;
   out_7295826236279740984[252] = 0;
   out_7295826236279740984[253] = 0;
   out_7295826236279740984[254] = 0;
   out_7295826236279740984[255] = 0;
   out_7295826236279740984[256] = 0;
   out_7295826236279740984[257] = 0;
   out_7295826236279740984[258] = 0;
   out_7295826236279740984[259] = 0;
   out_7295826236279740984[260] = 0;
   out_7295826236279740984[261] = 0;
   out_7295826236279740984[262] = 0;
   out_7295826236279740984[263] = 0;
   out_7295826236279740984[264] = 0;
   out_7295826236279740984[265] = 0;
   out_7295826236279740984[266] = 1;
   out_7295826236279740984[267] = 0;
   out_7295826236279740984[268] = 0;
   out_7295826236279740984[269] = 0;
   out_7295826236279740984[270] = 0;
   out_7295826236279740984[271] = 0;
   out_7295826236279740984[272] = 0;
   out_7295826236279740984[273] = 0;
   out_7295826236279740984[274] = 0;
   out_7295826236279740984[275] = 0;
   out_7295826236279740984[276] = 0;
   out_7295826236279740984[277] = 0;
   out_7295826236279740984[278] = 0;
   out_7295826236279740984[279] = 0;
   out_7295826236279740984[280] = 0;
   out_7295826236279740984[281] = 0;
   out_7295826236279740984[282] = 0;
   out_7295826236279740984[283] = 0;
   out_7295826236279740984[284] = 0;
   out_7295826236279740984[285] = 1;
   out_7295826236279740984[286] = 0;
   out_7295826236279740984[287] = 0;
   out_7295826236279740984[288] = 0;
   out_7295826236279740984[289] = 0;
   out_7295826236279740984[290] = 0;
   out_7295826236279740984[291] = 0;
   out_7295826236279740984[292] = 0;
   out_7295826236279740984[293] = 0;
   out_7295826236279740984[294] = 0;
   out_7295826236279740984[295] = 0;
   out_7295826236279740984[296] = 0;
   out_7295826236279740984[297] = 0;
   out_7295826236279740984[298] = 0;
   out_7295826236279740984[299] = 0;
   out_7295826236279740984[300] = 0;
   out_7295826236279740984[301] = 0;
   out_7295826236279740984[302] = 0;
   out_7295826236279740984[303] = 0;
   out_7295826236279740984[304] = 1;
   out_7295826236279740984[305] = 0;
   out_7295826236279740984[306] = 0;
   out_7295826236279740984[307] = 0;
   out_7295826236279740984[308] = 0;
   out_7295826236279740984[309] = 0;
   out_7295826236279740984[310] = 0;
   out_7295826236279740984[311] = 0;
   out_7295826236279740984[312] = 0;
   out_7295826236279740984[313] = 0;
   out_7295826236279740984[314] = 0;
   out_7295826236279740984[315] = 0;
   out_7295826236279740984[316] = 0;
   out_7295826236279740984[317] = 0;
   out_7295826236279740984[318] = 0;
   out_7295826236279740984[319] = 0;
   out_7295826236279740984[320] = 0;
   out_7295826236279740984[321] = 0;
   out_7295826236279740984[322] = 0;
   out_7295826236279740984[323] = 1;
}
void h_4(double *state, double *unused, double *out_3793117268866733474) {
   out_3793117268866733474[0] = state[6] + state[9];
   out_3793117268866733474[1] = state[7] + state[10];
   out_3793117268866733474[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_5018797825701000655) {
   out_5018797825701000655[0] = 0;
   out_5018797825701000655[1] = 0;
   out_5018797825701000655[2] = 0;
   out_5018797825701000655[3] = 0;
   out_5018797825701000655[4] = 0;
   out_5018797825701000655[5] = 0;
   out_5018797825701000655[6] = 1;
   out_5018797825701000655[7] = 0;
   out_5018797825701000655[8] = 0;
   out_5018797825701000655[9] = 1;
   out_5018797825701000655[10] = 0;
   out_5018797825701000655[11] = 0;
   out_5018797825701000655[12] = 0;
   out_5018797825701000655[13] = 0;
   out_5018797825701000655[14] = 0;
   out_5018797825701000655[15] = 0;
   out_5018797825701000655[16] = 0;
   out_5018797825701000655[17] = 0;
   out_5018797825701000655[18] = 0;
   out_5018797825701000655[19] = 0;
   out_5018797825701000655[20] = 0;
   out_5018797825701000655[21] = 0;
   out_5018797825701000655[22] = 0;
   out_5018797825701000655[23] = 0;
   out_5018797825701000655[24] = 0;
   out_5018797825701000655[25] = 1;
   out_5018797825701000655[26] = 0;
   out_5018797825701000655[27] = 0;
   out_5018797825701000655[28] = 1;
   out_5018797825701000655[29] = 0;
   out_5018797825701000655[30] = 0;
   out_5018797825701000655[31] = 0;
   out_5018797825701000655[32] = 0;
   out_5018797825701000655[33] = 0;
   out_5018797825701000655[34] = 0;
   out_5018797825701000655[35] = 0;
   out_5018797825701000655[36] = 0;
   out_5018797825701000655[37] = 0;
   out_5018797825701000655[38] = 0;
   out_5018797825701000655[39] = 0;
   out_5018797825701000655[40] = 0;
   out_5018797825701000655[41] = 0;
   out_5018797825701000655[42] = 0;
   out_5018797825701000655[43] = 0;
   out_5018797825701000655[44] = 1;
   out_5018797825701000655[45] = 0;
   out_5018797825701000655[46] = 0;
   out_5018797825701000655[47] = 1;
   out_5018797825701000655[48] = 0;
   out_5018797825701000655[49] = 0;
   out_5018797825701000655[50] = 0;
   out_5018797825701000655[51] = 0;
   out_5018797825701000655[52] = 0;
   out_5018797825701000655[53] = 0;
}
void h_10(double *state, double *unused, double *out_8131512363421803191) {
   out_8131512363421803191[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_8131512363421803191[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_8131512363421803191[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8940915420831957940) {
   out_8940915420831957940[0] = 0;
   out_8940915420831957940[1] = 9.8100000000000005*cos(state[1]);
   out_8940915420831957940[2] = 0;
   out_8940915420831957940[3] = 0;
   out_8940915420831957940[4] = -state[8];
   out_8940915420831957940[5] = state[7];
   out_8940915420831957940[6] = 0;
   out_8940915420831957940[7] = state[5];
   out_8940915420831957940[8] = -state[4];
   out_8940915420831957940[9] = 0;
   out_8940915420831957940[10] = 0;
   out_8940915420831957940[11] = 0;
   out_8940915420831957940[12] = 1;
   out_8940915420831957940[13] = 0;
   out_8940915420831957940[14] = 0;
   out_8940915420831957940[15] = 1;
   out_8940915420831957940[16] = 0;
   out_8940915420831957940[17] = 0;
   out_8940915420831957940[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8940915420831957940[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8940915420831957940[20] = 0;
   out_8940915420831957940[21] = state[8];
   out_8940915420831957940[22] = 0;
   out_8940915420831957940[23] = -state[6];
   out_8940915420831957940[24] = -state[5];
   out_8940915420831957940[25] = 0;
   out_8940915420831957940[26] = state[3];
   out_8940915420831957940[27] = 0;
   out_8940915420831957940[28] = 0;
   out_8940915420831957940[29] = 0;
   out_8940915420831957940[30] = 0;
   out_8940915420831957940[31] = 1;
   out_8940915420831957940[32] = 0;
   out_8940915420831957940[33] = 0;
   out_8940915420831957940[34] = 1;
   out_8940915420831957940[35] = 0;
   out_8940915420831957940[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8940915420831957940[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8940915420831957940[38] = 0;
   out_8940915420831957940[39] = -state[7];
   out_8940915420831957940[40] = state[6];
   out_8940915420831957940[41] = 0;
   out_8940915420831957940[42] = state[4];
   out_8940915420831957940[43] = -state[3];
   out_8940915420831957940[44] = 0;
   out_8940915420831957940[45] = 0;
   out_8940915420831957940[46] = 0;
   out_8940915420831957940[47] = 0;
   out_8940915420831957940[48] = 0;
   out_8940915420831957940[49] = 0;
   out_8940915420831957940[50] = 1;
   out_8940915420831957940[51] = 0;
   out_8940915420831957940[52] = 0;
   out_8940915420831957940[53] = 1;
}
void h_13(double *state, double *unused, double *out_686674294679068388) {
   out_686674294679068388[0] = state[3];
   out_686674294679068388[1] = state[4];
   out_686674294679068388[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8852553289003524679) {
   out_8852553289003524679[0] = 0;
   out_8852553289003524679[1] = 0;
   out_8852553289003524679[2] = 0;
   out_8852553289003524679[3] = 1;
   out_8852553289003524679[4] = 0;
   out_8852553289003524679[5] = 0;
   out_8852553289003524679[6] = 0;
   out_8852553289003524679[7] = 0;
   out_8852553289003524679[8] = 0;
   out_8852553289003524679[9] = 0;
   out_8852553289003524679[10] = 0;
   out_8852553289003524679[11] = 0;
   out_8852553289003524679[12] = 0;
   out_8852553289003524679[13] = 0;
   out_8852553289003524679[14] = 0;
   out_8852553289003524679[15] = 0;
   out_8852553289003524679[16] = 0;
   out_8852553289003524679[17] = 0;
   out_8852553289003524679[18] = 0;
   out_8852553289003524679[19] = 0;
   out_8852553289003524679[20] = 0;
   out_8852553289003524679[21] = 0;
   out_8852553289003524679[22] = 1;
   out_8852553289003524679[23] = 0;
   out_8852553289003524679[24] = 0;
   out_8852553289003524679[25] = 0;
   out_8852553289003524679[26] = 0;
   out_8852553289003524679[27] = 0;
   out_8852553289003524679[28] = 0;
   out_8852553289003524679[29] = 0;
   out_8852553289003524679[30] = 0;
   out_8852553289003524679[31] = 0;
   out_8852553289003524679[32] = 0;
   out_8852553289003524679[33] = 0;
   out_8852553289003524679[34] = 0;
   out_8852553289003524679[35] = 0;
   out_8852553289003524679[36] = 0;
   out_8852553289003524679[37] = 0;
   out_8852553289003524679[38] = 0;
   out_8852553289003524679[39] = 0;
   out_8852553289003524679[40] = 0;
   out_8852553289003524679[41] = 1;
   out_8852553289003524679[42] = 0;
   out_8852553289003524679[43] = 0;
   out_8852553289003524679[44] = 0;
   out_8852553289003524679[45] = 0;
   out_8852553289003524679[46] = 0;
   out_8852553289003524679[47] = 0;
   out_8852553289003524679[48] = 0;
   out_8852553289003524679[49] = 0;
   out_8852553289003524679[50] = 0;
   out_8852553289003524679[51] = 0;
   out_8852553289003524679[52] = 0;
   out_8852553289003524679[53] = 0;
}
void h_14(double *state, double *unused, double *out_4260835658611653154) {
   out_4260835658611653154[0] = state[6];
   out_4260835658611653154[1] = state[7];
   out_4260835658611653154[2] = state[8];
}
void H_14(double *state, double *unused, double *out_8101586257996372951) {
   out_8101586257996372951[0] = 0;
   out_8101586257996372951[1] = 0;
   out_8101586257996372951[2] = 0;
   out_8101586257996372951[3] = 0;
   out_8101586257996372951[4] = 0;
   out_8101586257996372951[5] = 0;
   out_8101586257996372951[6] = 1;
   out_8101586257996372951[7] = 0;
   out_8101586257996372951[8] = 0;
   out_8101586257996372951[9] = 0;
   out_8101586257996372951[10] = 0;
   out_8101586257996372951[11] = 0;
   out_8101586257996372951[12] = 0;
   out_8101586257996372951[13] = 0;
   out_8101586257996372951[14] = 0;
   out_8101586257996372951[15] = 0;
   out_8101586257996372951[16] = 0;
   out_8101586257996372951[17] = 0;
   out_8101586257996372951[18] = 0;
   out_8101586257996372951[19] = 0;
   out_8101586257996372951[20] = 0;
   out_8101586257996372951[21] = 0;
   out_8101586257996372951[22] = 0;
   out_8101586257996372951[23] = 0;
   out_8101586257996372951[24] = 0;
   out_8101586257996372951[25] = 1;
   out_8101586257996372951[26] = 0;
   out_8101586257996372951[27] = 0;
   out_8101586257996372951[28] = 0;
   out_8101586257996372951[29] = 0;
   out_8101586257996372951[30] = 0;
   out_8101586257996372951[31] = 0;
   out_8101586257996372951[32] = 0;
   out_8101586257996372951[33] = 0;
   out_8101586257996372951[34] = 0;
   out_8101586257996372951[35] = 0;
   out_8101586257996372951[36] = 0;
   out_8101586257996372951[37] = 0;
   out_8101586257996372951[38] = 0;
   out_8101586257996372951[39] = 0;
   out_8101586257996372951[40] = 0;
   out_8101586257996372951[41] = 0;
   out_8101586257996372951[42] = 0;
   out_8101586257996372951[43] = 0;
   out_8101586257996372951[44] = 1;
   out_8101586257996372951[45] = 0;
   out_8101586257996372951[46] = 0;
   out_8101586257996372951[47] = 0;
   out_8101586257996372951[48] = 0;
   out_8101586257996372951[49] = 0;
   out_8101586257996372951[50] = 0;
   out_8101586257996372951[51] = 0;
   out_8101586257996372951[52] = 0;
   out_8101586257996372951[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_494363428253979517) {
  err_fun(nom_x, delta_x, out_494363428253979517);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7744180703950466915) {
  inv_err_fun(nom_x, true_x, out_7744180703950466915);
}
void pose_H_mod_fun(double *state, double *out_8790605035544908227) {
  H_mod_fun(state, out_8790605035544908227);
}
void pose_f_fun(double *state, double dt, double *out_4191169391561892498) {
  f_fun(state,  dt, out_4191169391561892498);
}
void pose_F_fun(double *state, double dt, double *out_7295826236279740984) {
  F_fun(state,  dt, out_7295826236279740984);
}
void pose_h_4(double *state, double *unused, double *out_3793117268866733474) {
  h_4(state, unused, out_3793117268866733474);
}
void pose_H_4(double *state, double *unused, double *out_5018797825701000655) {
  H_4(state, unused, out_5018797825701000655);
}
void pose_h_10(double *state, double *unused, double *out_8131512363421803191) {
  h_10(state, unused, out_8131512363421803191);
}
void pose_H_10(double *state, double *unused, double *out_8940915420831957940) {
  H_10(state, unused, out_8940915420831957940);
}
void pose_h_13(double *state, double *unused, double *out_686674294679068388) {
  h_13(state, unused, out_686674294679068388);
}
void pose_H_13(double *state, double *unused, double *out_8852553289003524679) {
  H_13(state, unused, out_8852553289003524679);
}
void pose_h_14(double *state, double *unused, double *out_4260835658611653154) {
  h_14(state, unused, out_4260835658611653154);
}
void pose_H_14(double *state, double *unused, double *out_8101586257996372951) {
  H_14(state, unused, out_8101586257996372951);
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
