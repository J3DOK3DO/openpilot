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
void err_fun(double *nom_x, double *delta_x, double *out_6672914167572980790) {
   out_6672914167572980790[0] = delta_x[0] + nom_x[0];
   out_6672914167572980790[1] = delta_x[1] + nom_x[1];
   out_6672914167572980790[2] = delta_x[2] + nom_x[2];
   out_6672914167572980790[3] = delta_x[3] + nom_x[3];
   out_6672914167572980790[4] = delta_x[4] + nom_x[4];
   out_6672914167572980790[5] = delta_x[5] + nom_x[5];
   out_6672914167572980790[6] = delta_x[6] + nom_x[6];
   out_6672914167572980790[7] = delta_x[7] + nom_x[7];
   out_6672914167572980790[8] = delta_x[8] + nom_x[8];
   out_6672914167572980790[9] = delta_x[9] + nom_x[9];
   out_6672914167572980790[10] = delta_x[10] + nom_x[10];
   out_6672914167572980790[11] = delta_x[11] + nom_x[11];
   out_6672914167572980790[12] = delta_x[12] + nom_x[12];
   out_6672914167572980790[13] = delta_x[13] + nom_x[13];
   out_6672914167572980790[14] = delta_x[14] + nom_x[14];
   out_6672914167572980790[15] = delta_x[15] + nom_x[15];
   out_6672914167572980790[16] = delta_x[16] + nom_x[16];
   out_6672914167572980790[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7750354326522111493) {
   out_7750354326522111493[0] = -nom_x[0] + true_x[0];
   out_7750354326522111493[1] = -nom_x[1] + true_x[1];
   out_7750354326522111493[2] = -nom_x[2] + true_x[2];
   out_7750354326522111493[3] = -nom_x[3] + true_x[3];
   out_7750354326522111493[4] = -nom_x[4] + true_x[4];
   out_7750354326522111493[5] = -nom_x[5] + true_x[5];
   out_7750354326522111493[6] = -nom_x[6] + true_x[6];
   out_7750354326522111493[7] = -nom_x[7] + true_x[7];
   out_7750354326522111493[8] = -nom_x[8] + true_x[8];
   out_7750354326522111493[9] = -nom_x[9] + true_x[9];
   out_7750354326522111493[10] = -nom_x[10] + true_x[10];
   out_7750354326522111493[11] = -nom_x[11] + true_x[11];
   out_7750354326522111493[12] = -nom_x[12] + true_x[12];
   out_7750354326522111493[13] = -nom_x[13] + true_x[13];
   out_7750354326522111493[14] = -nom_x[14] + true_x[14];
   out_7750354326522111493[15] = -nom_x[15] + true_x[15];
   out_7750354326522111493[16] = -nom_x[16] + true_x[16];
   out_7750354326522111493[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_839860879621378337) {
   out_839860879621378337[0] = 1.0;
   out_839860879621378337[1] = 0.0;
   out_839860879621378337[2] = 0.0;
   out_839860879621378337[3] = 0.0;
   out_839860879621378337[4] = 0.0;
   out_839860879621378337[5] = 0.0;
   out_839860879621378337[6] = 0.0;
   out_839860879621378337[7] = 0.0;
   out_839860879621378337[8] = 0.0;
   out_839860879621378337[9] = 0.0;
   out_839860879621378337[10] = 0.0;
   out_839860879621378337[11] = 0.0;
   out_839860879621378337[12] = 0.0;
   out_839860879621378337[13] = 0.0;
   out_839860879621378337[14] = 0.0;
   out_839860879621378337[15] = 0.0;
   out_839860879621378337[16] = 0.0;
   out_839860879621378337[17] = 0.0;
   out_839860879621378337[18] = 0.0;
   out_839860879621378337[19] = 1.0;
   out_839860879621378337[20] = 0.0;
   out_839860879621378337[21] = 0.0;
   out_839860879621378337[22] = 0.0;
   out_839860879621378337[23] = 0.0;
   out_839860879621378337[24] = 0.0;
   out_839860879621378337[25] = 0.0;
   out_839860879621378337[26] = 0.0;
   out_839860879621378337[27] = 0.0;
   out_839860879621378337[28] = 0.0;
   out_839860879621378337[29] = 0.0;
   out_839860879621378337[30] = 0.0;
   out_839860879621378337[31] = 0.0;
   out_839860879621378337[32] = 0.0;
   out_839860879621378337[33] = 0.0;
   out_839860879621378337[34] = 0.0;
   out_839860879621378337[35] = 0.0;
   out_839860879621378337[36] = 0.0;
   out_839860879621378337[37] = 0.0;
   out_839860879621378337[38] = 1.0;
   out_839860879621378337[39] = 0.0;
   out_839860879621378337[40] = 0.0;
   out_839860879621378337[41] = 0.0;
   out_839860879621378337[42] = 0.0;
   out_839860879621378337[43] = 0.0;
   out_839860879621378337[44] = 0.0;
   out_839860879621378337[45] = 0.0;
   out_839860879621378337[46] = 0.0;
   out_839860879621378337[47] = 0.0;
   out_839860879621378337[48] = 0.0;
   out_839860879621378337[49] = 0.0;
   out_839860879621378337[50] = 0.0;
   out_839860879621378337[51] = 0.0;
   out_839860879621378337[52] = 0.0;
   out_839860879621378337[53] = 0.0;
   out_839860879621378337[54] = 0.0;
   out_839860879621378337[55] = 0.0;
   out_839860879621378337[56] = 0.0;
   out_839860879621378337[57] = 1.0;
   out_839860879621378337[58] = 0.0;
   out_839860879621378337[59] = 0.0;
   out_839860879621378337[60] = 0.0;
   out_839860879621378337[61] = 0.0;
   out_839860879621378337[62] = 0.0;
   out_839860879621378337[63] = 0.0;
   out_839860879621378337[64] = 0.0;
   out_839860879621378337[65] = 0.0;
   out_839860879621378337[66] = 0.0;
   out_839860879621378337[67] = 0.0;
   out_839860879621378337[68] = 0.0;
   out_839860879621378337[69] = 0.0;
   out_839860879621378337[70] = 0.0;
   out_839860879621378337[71] = 0.0;
   out_839860879621378337[72] = 0.0;
   out_839860879621378337[73] = 0.0;
   out_839860879621378337[74] = 0.0;
   out_839860879621378337[75] = 0.0;
   out_839860879621378337[76] = 1.0;
   out_839860879621378337[77] = 0.0;
   out_839860879621378337[78] = 0.0;
   out_839860879621378337[79] = 0.0;
   out_839860879621378337[80] = 0.0;
   out_839860879621378337[81] = 0.0;
   out_839860879621378337[82] = 0.0;
   out_839860879621378337[83] = 0.0;
   out_839860879621378337[84] = 0.0;
   out_839860879621378337[85] = 0.0;
   out_839860879621378337[86] = 0.0;
   out_839860879621378337[87] = 0.0;
   out_839860879621378337[88] = 0.0;
   out_839860879621378337[89] = 0.0;
   out_839860879621378337[90] = 0.0;
   out_839860879621378337[91] = 0.0;
   out_839860879621378337[92] = 0.0;
   out_839860879621378337[93] = 0.0;
   out_839860879621378337[94] = 0.0;
   out_839860879621378337[95] = 1.0;
   out_839860879621378337[96] = 0.0;
   out_839860879621378337[97] = 0.0;
   out_839860879621378337[98] = 0.0;
   out_839860879621378337[99] = 0.0;
   out_839860879621378337[100] = 0.0;
   out_839860879621378337[101] = 0.0;
   out_839860879621378337[102] = 0.0;
   out_839860879621378337[103] = 0.0;
   out_839860879621378337[104] = 0.0;
   out_839860879621378337[105] = 0.0;
   out_839860879621378337[106] = 0.0;
   out_839860879621378337[107] = 0.0;
   out_839860879621378337[108] = 0.0;
   out_839860879621378337[109] = 0.0;
   out_839860879621378337[110] = 0.0;
   out_839860879621378337[111] = 0.0;
   out_839860879621378337[112] = 0.0;
   out_839860879621378337[113] = 0.0;
   out_839860879621378337[114] = 1.0;
   out_839860879621378337[115] = 0.0;
   out_839860879621378337[116] = 0.0;
   out_839860879621378337[117] = 0.0;
   out_839860879621378337[118] = 0.0;
   out_839860879621378337[119] = 0.0;
   out_839860879621378337[120] = 0.0;
   out_839860879621378337[121] = 0.0;
   out_839860879621378337[122] = 0.0;
   out_839860879621378337[123] = 0.0;
   out_839860879621378337[124] = 0.0;
   out_839860879621378337[125] = 0.0;
   out_839860879621378337[126] = 0.0;
   out_839860879621378337[127] = 0.0;
   out_839860879621378337[128] = 0.0;
   out_839860879621378337[129] = 0.0;
   out_839860879621378337[130] = 0.0;
   out_839860879621378337[131] = 0.0;
   out_839860879621378337[132] = 0.0;
   out_839860879621378337[133] = 1.0;
   out_839860879621378337[134] = 0.0;
   out_839860879621378337[135] = 0.0;
   out_839860879621378337[136] = 0.0;
   out_839860879621378337[137] = 0.0;
   out_839860879621378337[138] = 0.0;
   out_839860879621378337[139] = 0.0;
   out_839860879621378337[140] = 0.0;
   out_839860879621378337[141] = 0.0;
   out_839860879621378337[142] = 0.0;
   out_839860879621378337[143] = 0.0;
   out_839860879621378337[144] = 0.0;
   out_839860879621378337[145] = 0.0;
   out_839860879621378337[146] = 0.0;
   out_839860879621378337[147] = 0.0;
   out_839860879621378337[148] = 0.0;
   out_839860879621378337[149] = 0.0;
   out_839860879621378337[150] = 0.0;
   out_839860879621378337[151] = 0.0;
   out_839860879621378337[152] = 1.0;
   out_839860879621378337[153] = 0.0;
   out_839860879621378337[154] = 0.0;
   out_839860879621378337[155] = 0.0;
   out_839860879621378337[156] = 0.0;
   out_839860879621378337[157] = 0.0;
   out_839860879621378337[158] = 0.0;
   out_839860879621378337[159] = 0.0;
   out_839860879621378337[160] = 0.0;
   out_839860879621378337[161] = 0.0;
   out_839860879621378337[162] = 0.0;
   out_839860879621378337[163] = 0.0;
   out_839860879621378337[164] = 0.0;
   out_839860879621378337[165] = 0.0;
   out_839860879621378337[166] = 0.0;
   out_839860879621378337[167] = 0.0;
   out_839860879621378337[168] = 0.0;
   out_839860879621378337[169] = 0.0;
   out_839860879621378337[170] = 0.0;
   out_839860879621378337[171] = 1.0;
   out_839860879621378337[172] = 0.0;
   out_839860879621378337[173] = 0.0;
   out_839860879621378337[174] = 0.0;
   out_839860879621378337[175] = 0.0;
   out_839860879621378337[176] = 0.0;
   out_839860879621378337[177] = 0.0;
   out_839860879621378337[178] = 0.0;
   out_839860879621378337[179] = 0.0;
   out_839860879621378337[180] = 0.0;
   out_839860879621378337[181] = 0.0;
   out_839860879621378337[182] = 0.0;
   out_839860879621378337[183] = 0.0;
   out_839860879621378337[184] = 0.0;
   out_839860879621378337[185] = 0.0;
   out_839860879621378337[186] = 0.0;
   out_839860879621378337[187] = 0.0;
   out_839860879621378337[188] = 0.0;
   out_839860879621378337[189] = 0.0;
   out_839860879621378337[190] = 1.0;
   out_839860879621378337[191] = 0.0;
   out_839860879621378337[192] = 0.0;
   out_839860879621378337[193] = 0.0;
   out_839860879621378337[194] = 0.0;
   out_839860879621378337[195] = 0.0;
   out_839860879621378337[196] = 0.0;
   out_839860879621378337[197] = 0.0;
   out_839860879621378337[198] = 0.0;
   out_839860879621378337[199] = 0.0;
   out_839860879621378337[200] = 0.0;
   out_839860879621378337[201] = 0.0;
   out_839860879621378337[202] = 0.0;
   out_839860879621378337[203] = 0.0;
   out_839860879621378337[204] = 0.0;
   out_839860879621378337[205] = 0.0;
   out_839860879621378337[206] = 0.0;
   out_839860879621378337[207] = 0.0;
   out_839860879621378337[208] = 0.0;
   out_839860879621378337[209] = 1.0;
   out_839860879621378337[210] = 0.0;
   out_839860879621378337[211] = 0.0;
   out_839860879621378337[212] = 0.0;
   out_839860879621378337[213] = 0.0;
   out_839860879621378337[214] = 0.0;
   out_839860879621378337[215] = 0.0;
   out_839860879621378337[216] = 0.0;
   out_839860879621378337[217] = 0.0;
   out_839860879621378337[218] = 0.0;
   out_839860879621378337[219] = 0.0;
   out_839860879621378337[220] = 0.0;
   out_839860879621378337[221] = 0.0;
   out_839860879621378337[222] = 0.0;
   out_839860879621378337[223] = 0.0;
   out_839860879621378337[224] = 0.0;
   out_839860879621378337[225] = 0.0;
   out_839860879621378337[226] = 0.0;
   out_839860879621378337[227] = 0.0;
   out_839860879621378337[228] = 1.0;
   out_839860879621378337[229] = 0.0;
   out_839860879621378337[230] = 0.0;
   out_839860879621378337[231] = 0.0;
   out_839860879621378337[232] = 0.0;
   out_839860879621378337[233] = 0.0;
   out_839860879621378337[234] = 0.0;
   out_839860879621378337[235] = 0.0;
   out_839860879621378337[236] = 0.0;
   out_839860879621378337[237] = 0.0;
   out_839860879621378337[238] = 0.0;
   out_839860879621378337[239] = 0.0;
   out_839860879621378337[240] = 0.0;
   out_839860879621378337[241] = 0.0;
   out_839860879621378337[242] = 0.0;
   out_839860879621378337[243] = 0.0;
   out_839860879621378337[244] = 0.0;
   out_839860879621378337[245] = 0.0;
   out_839860879621378337[246] = 0.0;
   out_839860879621378337[247] = 1.0;
   out_839860879621378337[248] = 0.0;
   out_839860879621378337[249] = 0.0;
   out_839860879621378337[250] = 0.0;
   out_839860879621378337[251] = 0.0;
   out_839860879621378337[252] = 0.0;
   out_839860879621378337[253] = 0.0;
   out_839860879621378337[254] = 0.0;
   out_839860879621378337[255] = 0.0;
   out_839860879621378337[256] = 0.0;
   out_839860879621378337[257] = 0.0;
   out_839860879621378337[258] = 0.0;
   out_839860879621378337[259] = 0.0;
   out_839860879621378337[260] = 0.0;
   out_839860879621378337[261] = 0.0;
   out_839860879621378337[262] = 0.0;
   out_839860879621378337[263] = 0.0;
   out_839860879621378337[264] = 0.0;
   out_839860879621378337[265] = 0.0;
   out_839860879621378337[266] = 1.0;
   out_839860879621378337[267] = 0.0;
   out_839860879621378337[268] = 0.0;
   out_839860879621378337[269] = 0.0;
   out_839860879621378337[270] = 0.0;
   out_839860879621378337[271] = 0.0;
   out_839860879621378337[272] = 0.0;
   out_839860879621378337[273] = 0.0;
   out_839860879621378337[274] = 0.0;
   out_839860879621378337[275] = 0.0;
   out_839860879621378337[276] = 0.0;
   out_839860879621378337[277] = 0.0;
   out_839860879621378337[278] = 0.0;
   out_839860879621378337[279] = 0.0;
   out_839860879621378337[280] = 0.0;
   out_839860879621378337[281] = 0.0;
   out_839860879621378337[282] = 0.0;
   out_839860879621378337[283] = 0.0;
   out_839860879621378337[284] = 0.0;
   out_839860879621378337[285] = 1.0;
   out_839860879621378337[286] = 0.0;
   out_839860879621378337[287] = 0.0;
   out_839860879621378337[288] = 0.0;
   out_839860879621378337[289] = 0.0;
   out_839860879621378337[290] = 0.0;
   out_839860879621378337[291] = 0.0;
   out_839860879621378337[292] = 0.0;
   out_839860879621378337[293] = 0.0;
   out_839860879621378337[294] = 0.0;
   out_839860879621378337[295] = 0.0;
   out_839860879621378337[296] = 0.0;
   out_839860879621378337[297] = 0.0;
   out_839860879621378337[298] = 0.0;
   out_839860879621378337[299] = 0.0;
   out_839860879621378337[300] = 0.0;
   out_839860879621378337[301] = 0.0;
   out_839860879621378337[302] = 0.0;
   out_839860879621378337[303] = 0.0;
   out_839860879621378337[304] = 1.0;
   out_839860879621378337[305] = 0.0;
   out_839860879621378337[306] = 0.0;
   out_839860879621378337[307] = 0.0;
   out_839860879621378337[308] = 0.0;
   out_839860879621378337[309] = 0.0;
   out_839860879621378337[310] = 0.0;
   out_839860879621378337[311] = 0.0;
   out_839860879621378337[312] = 0.0;
   out_839860879621378337[313] = 0.0;
   out_839860879621378337[314] = 0.0;
   out_839860879621378337[315] = 0.0;
   out_839860879621378337[316] = 0.0;
   out_839860879621378337[317] = 0.0;
   out_839860879621378337[318] = 0.0;
   out_839860879621378337[319] = 0.0;
   out_839860879621378337[320] = 0.0;
   out_839860879621378337[321] = 0.0;
   out_839860879621378337[322] = 0.0;
   out_839860879621378337[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4259182462982083528) {
   out_4259182462982083528[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4259182462982083528[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4259182462982083528[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4259182462982083528[3] = dt*state[12] + state[3];
   out_4259182462982083528[4] = dt*state[13] + state[4];
   out_4259182462982083528[5] = dt*state[14] + state[5];
   out_4259182462982083528[6] = state[6];
   out_4259182462982083528[7] = state[7];
   out_4259182462982083528[8] = state[8];
   out_4259182462982083528[9] = state[9];
   out_4259182462982083528[10] = state[10];
   out_4259182462982083528[11] = state[11];
   out_4259182462982083528[12] = state[12];
   out_4259182462982083528[13] = state[13];
   out_4259182462982083528[14] = state[14];
   out_4259182462982083528[15] = state[15];
   out_4259182462982083528[16] = state[16];
   out_4259182462982083528[17] = state[17];
}
void F_fun(double *state, double dt, double *out_3243909512724105051) {
   out_3243909512724105051[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3243909512724105051[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3243909512724105051[2] = 0;
   out_3243909512724105051[3] = 0;
   out_3243909512724105051[4] = 0;
   out_3243909512724105051[5] = 0;
   out_3243909512724105051[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3243909512724105051[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3243909512724105051[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3243909512724105051[9] = 0;
   out_3243909512724105051[10] = 0;
   out_3243909512724105051[11] = 0;
   out_3243909512724105051[12] = 0;
   out_3243909512724105051[13] = 0;
   out_3243909512724105051[14] = 0;
   out_3243909512724105051[15] = 0;
   out_3243909512724105051[16] = 0;
   out_3243909512724105051[17] = 0;
   out_3243909512724105051[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3243909512724105051[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3243909512724105051[20] = 0;
   out_3243909512724105051[21] = 0;
   out_3243909512724105051[22] = 0;
   out_3243909512724105051[23] = 0;
   out_3243909512724105051[24] = 0;
   out_3243909512724105051[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3243909512724105051[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3243909512724105051[27] = 0;
   out_3243909512724105051[28] = 0;
   out_3243909512724105051[29] = 0;
   out_3243909512724105051[30] = 0;
   out_3243909512724105051[31] = 0;
   out_3243909512724105051[32] = 0;
   out_3243909512724105051[33] = 0;
   out_3243909512724105051[34] = 0;
   out_3243909512724105051[35] = 0;
   out_3243909512724105051[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3243909512724105051[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3243909512724105051[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3243909512724105051[39] = 0;
   out_3243909512724105051[40] = 0;
   out_3243909512724105051[41] = 0;
   out_3243909512724105051[42] = 0;
   out_3243909512724105051[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3243909512724105051[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3243909512724105051[45] = 0;
   out_3243909512724105051[46] = 0;
   out_3243909512724105051[47] = 0;
   out_3243909512724105051[48] = 0;
   out_3243909512724105051[49] = 0;
   out_3243909512724105051[50] = 0;
   out_3243909512724105051[51] = 0;
   out_3243909512724105051[52] = 0;
   out_3243909512724105051[53] = 0;
   out_3243909512724105051[54] = 0;
   out_3243909512724105051[55] = 0;
   out_3243909512724105051[56] = 0;
   out_3243909512724105051[57] = 1;
   out_3243909512724105051[58] = 0;
   out_3243909512724105051[59] = 0;
   out_3243909512724105051[60] = 0;
   out_3243909512724105051[61] = 0;
   out_3243909512724105051[62] = 0;
   out_3243909512724105051[63] = 0;
   out_3243909512724105051[64] = 0;
   out_3243909512724105051[65] = 0;
   out_3243909512724105051[66] = dt;
   out_3243909512724105051[67] = 0;
   out_3243909512724105051[68] = 0;
   out_3243909512724105051[69] = 0;
   out_3243909512724105051[70] = 0;
   out_3243909512724105051[71] = 0;
   out_3243909512724105051[72] = 0;
   out_3243909512724105051[73] = 0;
   out_3243909512724105051[74] = 0;
   out_3243909512724105051[75] = 0;
   out_3243909512724105051[76] = 1;
   out_3243909512724105051[77] = 0;
   out_3243909512724105051[78] = 0;
   out_3243909512724105051[79] = 0;
   out_3243909512724105051[80] = 0;
   out_3243909512724105051[81] = 0;
   out_3243909512724105051[82] = 0;
   out_3243909512724105051[83] = 0;
   out_3243909512724105051[84] = 0;
   out_3243909512724105051[85] = dt;
   out_3243909512724105051[86] = 0;
   out_3243909512724105051[87] = 0;
   out_3243909512724105051[88] = 0;
   out_3243909512724105051[89] = 0;
   out_3243909512724105051[90] = 0;
   out_3243909512724105051[91] = 0;
   out_3243909512724105051[92] = 0;
   out_3243909512724105051[93] = 0;
   out_3243909512724105051[94] = 0;
   out_3243909512724105051[95] = 1;
   out_3243909512724105051[96] = 0;
   out_3243909512724105051[97] = 0;
   out_3243909512724105051[98] = 0;
   out_3243909512724105051[99] = 0;
   out_3243909512724105051[100] = 0;
   out_3243909512724105051[101] = 0;
   out_3243909512724105051[102] = 0;
   out_3243909512724105051[103] = 0;
   out_3243909512724105051[104] = dt;
   out_3243909512724105051[105] = 0;
   out_3243909512724105051[106] = 0;
   out_3243909512724105051[107] = 0;
   out_3243909512724105051[108] = 0;
   out_3243909512724105051[109] = 0;
   out_3243909512724105051[110] = 0;
   out_3243909512724105051[111] = 0;
   out_3243909512724105051[112] = 0;
   out_3243909512724105051[113] = 0;
   out_3243909512724105051[114] = 1;
   out_3243909512724105051[115] = 0;
   out_3243909512724105051[116] = 0;
   out_3243909512724105051[117] = 0;
   out_3243909512724105051[118] = 0;
   out_3243909512724105051[119] = 0;
   out_3243909512724105051[120] = 0;
   out_3243909512724105051[121] = 0;
   out_3243909512724105051[122] = 0;
   out_3243909512724105051[123] = 0;
   out_3243909512724105051[124] = 0;
   out_3243909512724105051[125] = 0;
   out_3243909512724105051[126] = 0;
   out_3243909512724105051[127] = 0;
   out_3243909512724105051[128] = 0;
   out_3243909512724105051[129] = 0;
   out_3243909512724105051[130] = 0;
   out_3243909512724105051[131] = 0;
   out_3243909512724105051[132] = 0;
   out_3243909512724105051[133] = 1;
   out_3243909512724105051[134] = 0;
   out_3243909512724105051[135] = 0;
   out_3243909512724105051[136] = 0;
   out_3243909512724105051[137] = 0;
   out_3243909512724105051[138] = 0;
   out_3243909512724105051[139] = 0;
   out_3243909512724105051[140] = 0;
   out_3243909512724105051[141] = 0;
   out_3243909512724105051[142] = 0;
   out_3243909512724105051[143] = 0;
   out_3243909512724105051[144] = 0;
   out_3243909512724105051[145] = 0;
   out_3243909512724105051[146] = 0;
   out_3243909512724105051[147] = 0;
   out_3243909512724105051[148] = 0;
   out_3243909512724105051[149] = 0;
   out_3243909512724105051[150] = 0;
   out_3243909512724105051[151] = 0;
   out_3243909512724105051[152] = 1;
   out_3243909512724105051[153] = 0;
   out_3243909512724105051[154] = 0;
   out_3243909512724105051[155] = 0;
   out_3243909512724105051[156] = 0;
   out_3243909512724105051[157] = 0;
   out_3243909512724105051[158] = 0;
   out_3243909512724105051[159] = 0;
   out_3243909512724105051[160] = 0;
   out_3243909512724105051[161] = 0;
   out_3243909512724105051[162] = 0;
   out_3243909512724105051[163] = 0;
   out_3243909512724105051[164] = 0;
   out_3243909512724105051[165] = 0;
   out_3243909512724105051[166] = 0;
   out_3243909512724105051[167] = 0;
   out_3243909512724105051[168] = 0;
   out_3243909512724105051[169] = 0;
   out_3243909512724105051[170] = 0;
   out_3243909512724105051[171] = 1;
   out_3243909512724105051[172] = 0;
   out_3243909512724105051[173] = 0;
   out_3243909512724105051[174] = 0;
   out_3243909512724105051[175] = 0;
   out_3243909512724105051[176] = 0;
   out_3243909512724105051[177] = 0;
   out_3243909512724105051[178] = 0;
   out_3243909512724105051[179] = 0;
   out_3243909512724105051[180] = 0;
   out_3243909512724105051[181] = 0;
   out_3243909512724105051[182] = 0;
   out_3243909512724105051[183] = 0;
   out_3243909512724105051[184] = 0;
   out_3243909512724105051[185] = 0;
   out_3243909512724105051[186] = 0;
   out_3243909512724105051[187] = 0;
   out_3243909512724105051[188] = 0;
   out_3243909512724105051[189] = 0;
   out_3243909512724105051[190] = 1;
   out_3243909512724105051[191] = 0;
   out_3243909512724105051[192] = 0;
   out_3243909512724105051[193] = 0;
   out_3243909512724105051[194] = 0;
   out_3243909512724105051[195] = 0;
   out_3243909512724105051[196] = 0;
   out_3243909512724105051[197] = 0;
   out_3243909512724105051[198] = 0;
   out_3243909512724105051[199] = 0;
   out_3243909512724105051[200] = 0;
   out_3243909512724105051[201] = 0;
   out_3243909512724105051[202] = 0;
   out_3243909512724105051[203] = 0;
   out_3243909512724105051[204] = 0;
   out_3243909512724105051[205] = 0;
   out_3243909512724105051[206] = 0;
   out_3243909512724105051[207] = 0;
   out_3243909512724105051[208] = 0;
   out_3243909512724105051[209] = 1;
   out_3243909512724105051[210] = 0;
   out_3243909512724105051[211] = 0;
   out_3243909512724105051[212] = 0;
   out_3243909512724105051[213] = 0;
   out_3243909512724105051[214] = 0;
   out_3243909512724105051[215] = 0;
   out_3243909512724105051[216] = 0;
   out_3243909512724105051[217] = 0;
   out_3243909512724105051[218] = 0;
   out_3243909512724105051[219] = 0;
   out_3243909512724105051[220] = 0;
   out_3243909512724105051[221] = 0;
   out_3243909512724105051[222] = 0;
   out_3243909512724105051[223] = 0;
   out_3243909512724105051[224] = 0;
   out_3243909512724105051[225] = 0;
   out_3243909512724105051[226] = 0;
   out_3243909512724105051[227] = 0;
   out_3243909512724105051[228] = 1;
   out_3243909512724105051[229] = 0;
   out_3243909512724105051[230] = 0;
   out_3243909512724105051[231] = 0;
   out_3243909512724105051[232] = 0;
   out_3243909512724105051[233] = 0;
   out_3243909512724105051[234] = 0;
   out_3243909512724105051[235] = 0;
   out_3243909512724105051[236] = 0;
   out_3243909512724105051[237] = 0;
   out_3243909512724105051[238] = 0;
   out_3243909512724105051[239] = 0;
   out_3243909512724105051[240] = 0;
   out_3243909512724105051[241] = 0;
   out_3243909512724105051[242] = 0;
   out_3243909512724105051[243] = 0;
   out_3243909512724105051[244] = 0;
   out_3243909512724105051[245] = 0;
   out_3243909512724105051[246] = 0;
   out_3243909512724105051[247] = 1;
   out_3243909512724105051[248] = 0;
   out_3243909512724105051[249] = 0;
   out_3243909512724105051[250] = 0;
   out_3243909512724105051[251] = 0;
   out_3243909512724105051[252] = 0;
   out_3243909512724105051[253] = 0;
   out_3243909512724105051[254] = 0;
   out_3243909512724105051[255] = 0;
   out_3243909512724105051[256] = 0;
   out_3243909512724105051[257] = 0;
   out_3243909512724105051[258] = 0;
   out_3243909512724105051[259] = 0;
   out_3243909512724105051[260] = 0;
   out_3243909512724105051[261] = 0;
   out_3243909512724105051[262] = 0;
   out_3243909512724105051[263] = 0;
   out_3243909512724105051[264] = 0;
   out_3243909512724105051[265] = 0;
   out_3243909512724105051[266] = 1;
   out_3243909512724105051[267] = 0;
   out_3243909512724105051[268] = 0;
   out_3243909512724105051[269] = 0;
   out_3243909512724105051[270] = 0;
   out_3243909512724105051[271] = 0;
   out_3243909512724105051[272] = 0;
   out_3243909512724105051[273] = 0;
   out_3243909512724105051[274] = 0;
   out_3243909512724105051[275] = 0;
   out_3243909512724105051[276] = 0;
   out_3243909512724105051[277] = 0;
   out_3243909512724105051[278] = 0;
   out_3243909512724105051[279] = 0;
   out_3243909512724105051[280] = 0;
   out_3243909512724105051[281] = 0;
   out_3243909512724105051[282] = 0;
   out_3243909512724105051[283] = 0;
   out_3243909512724105051[284] = 0;
   out_3243909512724105051[285] = 1;
   out_3243909512724105051[286] = 0;
   out_3243909512724105051[287] = 0;
   out_3243909512724105051[288] = 0;
   out_3243909512724105051[289] = 0;
   out_3243909512724105051[290] = 0;
   out_3243909512724105051[291] = 0;
   out_3243909512724105051[292] = 0;
   out_3243909512724105051[293] = 0;
   out_3243909512724105051[294] = 0;
   out_3243909512724105051[295] = 0;
   out_3243909512724105051[296] = 0;
   out_3243909512724105051[297] = 0;
   out_3243909512724105051[298] = 0;
   out_3243909512724105051[299] = 0;
   out_3243909512724105051[300] = 0;
   out_3243909512724105051[301] = 0;
   out_3243909512724105051[302] = 0;
   out_3243909512724105051[303] = 0;
   out_3243909512724105051[304] = 1;
   out_3243909512724105051[305] = 0;
   out_3243909512724105051[306] = 0;
   out_3243909512724105051[307] = 0;
   out_3243909512724105051[308] = 0;
   out_3243909512724105051[309] = 0;
   out_3243909512724105051[310] = 0;
   out_3243909512724105051[311] = 0;
   out_3243909512724105051[312] = 0;
   out_3243909512724105051[313] = 0;
   out_3243909512724105051[314] = 0;
   out_3243909512724105051[315] = 0;
   out_3243909512724105051[316] = 0;
   out_3243909512724105051[317] = 0;
   out_3243909512724105051[318] = 0;
   out_3243909512724105051[319] = 0;
   out_3243909512724105051[320] = 0;
   out_3243909512724105051[321] = 0;
   out_3243909512724105051[322] = 0;
   out_3243909512724105051[323] = 1;
}
void h_4(double *state, double *unused, double *out_4501441890577505558) {
   out_4501441890577505558[0] = state[6] + state[9];
   out_4501441890577505558[1] = state[7] + state[10];
   out_4501441890577505558[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_957367488565514356) {
   out_957367488565514356[0] = 0;
   out_957367488565514356[1] = 0;
   out_957367488565514356[2] = 0;
   out_957367488565514356[3] = 0;
   out_957367488565514356[4] = 0;
   out_957367488565514356[5] = 0;
   out_957367488565514356[6] = 1;
   out_957367488565514356[7] = 0;
   out_957367488565514356[8] = 0;
   out_957367488565514356[9] = 1;
   out_957367488565514356[10] = 0;
   out_957367488565514356[11] = 0;
   out_957367488565514356[12] = 0;
   out_957367488565514356[13] = 0;
   out_957367488565514356[14] = 0;
   out_957367488565514356[15] = 0;
   out_957367488565514356[16] = 0;
   out_957367488565514356[17] = 0;
   out_957367488565514356[18] = 0;
   out_957367488565514356[19] = 0;
   out_957367488565514356[20] = 0;
   out_957367488565514356[21] = 0;
   out_957367488565514356[22] = 0;
   out_957367488565514356[23] = 0;
   out_957367488565514356[24] = 0;
   out_957367488565514356[25] = 1;
   out_957367488565514356[26] = 0;
   out_957367488565514356[27] = 0;
   out_957367488565514356[28] = 1;
   out_957367488565514356[29] = 0;
   out_957367488565514356[30] = 0;
   out_957367488565514356[31] = 0;
   out_957367488565514356[32] = 0;
   out_957367488565514356[33] = 0;
   out_957367488565514356[34] = 0;
   out_957367488565514356[35] = 0;
   out_957367488565514356[36] = 0;
   out_957367488565514356[37] = 0;
   out_957367488565514356[38] = 0;
   out_957367488565514356[39] = 0;
   out_957367488565514356[40] = 0;
   out_957367488565514356[41] = 0;
   out_957367488565514356[42] = 0;
   out_957367488565514356[43] = 0;
   out_957367488565514356[44] = 1;
   out_957367488565514356[45] = 0;
   out_957367488565514356[46] = 0;
   out_957367488565514356[47] = 1;
   out_957367488565514356[48] = 0;
   out_957367488565514356[49] = 0;
   out_957367488565514356[50] = 0;
   out_957367488565514356[51] = 0;
   out_957367488565514356[52] = 0;
   out_957367488565514356[53] = 0;
}
void h_10(double *state, double *unused, double *out_4701543042744826127) {
   out_4701543042744826127[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_4701543042744826127[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_4701543042744826127[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_1475315339015463538) {
   out_1475315339015463538[0] = 0;
   out_1475315339015463538[1] = 9.8100000000000005*cos(state[1]);
   out_1475315339015463538[2] = 0;
   out_1475315339015463538[3] = 0;
   out_1475315339015463538[4] = -state[8];
   out_1475315339015463538[5] = state[7];
   out_1475315339015463538[6] = 0;
   out_1475315339015463538[7] = state[5];
   out_1475315339015463538[8] = -state[4];
   out_1475315339015463538[9] = 0;
   out_1475315339015463538[10] = 0;
   out_1475315339015463538[11] = 0;
   out_1475315339015463538[12] = 1;
   out_1475315339015463538[13] = 0;
   out_1475315339015463538[14] = 0;
   out_1475315339015463538[15] = 1;
   out_1475315339015463538[16] = 0;
   out_1475315339015463538[17] = 0;
   out_1475315339015463538[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_1475315339015463538[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_1475315339015463538[20] = 0;
   out_1475315339015463538[21] = state[8];
   out_1475315339015463538[22] = 0;
   out_1475315339015463538[23] = -state[6];
   out_1475315339015463538[24] = -state[5];
   out_1475315339015463538[25] = 0;
   out_1475315339015463538[26] = state[3];
   out_1475315339015463538[27] = 0;
   out_1475315339015463538[28] = 0;
   out_1475315339015463538[29] = 0;
   out_1475315339015463538[30] = 0;
   out_1475315339015463538[31] = 1;
   out_1475315339015463538[32] = 0;
   out_1475315339015463538[33] = 0;
   out_1475315339015463538[34] = 1;
   out_1475315339015463538[35] = 0;
   out_1475315339015463538[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_1475315339015463538[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_1475315339015463538[38] = 0;
   out_1475315339015463538[39] = -state[7];
   out_1475315339015463538[40] = state[6];
   out_1475315339015463538[41] = 0;
   out_1475315339015463538[42] = state[4];
   out_1475315339015463538[43] = -state[3];
   out_1475315339015463538[44] = 0;
   out_1475315339015463538[45] = 0;
   out_1475315339015463538[46] = 0;
   out_1475315339015463538[47] = 0;
   out_1475315339015463538[48] = 0;
   out_1475315339015463538[49] = 0;
   out_1475315339015463538[50] = 1;
   out_1475315339015463538[51] = 0;
   out_1475315339015463538[52] = 0;
   out_1475315339015463538[53] = 1;
}
void h_13(double *state, double *unused, double *out_8766901177225402962) {
   out_8766901177225402962[0] = state[3];
   out_8766901177225402962[1] = state[4];
   out_8766901177225402962[2] = state[5];
}
void H_13(double *state, double *unused, double *out_2254906336766818445) {
   out_2254906336766818445[0] = 0;
   out_2254906336766818445[1] = 0;
   out_2254906336766818445[2] = 0;
   out_2254906336766818445[3] = 1;
   out_2254906336766818445[4] = 0;
   out_2254906336766818445[5] = 0;
   out_2254906336766818445[6] = 0;
   out_2254906336766818445[7] = 0;
   out_2254906336766818445[8] = 0;
   out_2254906336766818445[9] = 0;
   out_2254906336766818445[10] = 0;
   out_2254906336766818445[11] = 0;
   out_2254906336766818445[12] = 0;
   out_2254906336766818445[13] = 0;
   out_2254906336766818445[14] = 0;
   out_2254906336766818445[15] = 0;
   out_2254906336766818445[16] = 0;
   out_2254906336766818445[17] = 0;
   out_2254906336766818445[18] = 0;
   out_2254906336766818445[19] = 0;
   out_2254906336766818445[20] = 0;
   out_2254906336766818445[21] = 0;
   out_2254906336766818445[22] = 1;
   out_2254906336766818445[23] = 0;
   out_2254906336766818445[24] = 0;
   out_2254906336766818445[25] = 0;
   out_2254906336766818445[26] = 0;
   out_2254906336766818445[27] = 0;
   out_2254906336766818445[28] = 0;
   out_2254906336766818445[29] = 0;
   out_2254906336766818445[30] = 0;
   out_2254906336766818445[31] = 0;
   out_2254906336766818445[32] = 0;
   out_2254906336766818445[33] = 0;
   out_2254906336766818445[34] = 0;
   out_2254906336766818445[35] = 0;
   out_2254906336766818445[36] = 0;
   out_2254906336766818445[37] = 0;
   out_2254906336766818445[38] = 0;
   out_2254906336766818445[39] = 0;
   out_2254906336766818445[40] = 0;
   out_2254906336766818445[41] = 1;
   out_2254906336766818445[42] = 0;
   out_2254906336766818445[43] = 0;
   out_2254906336766818445[44] = 0;
   out_2254906336766818445[45] = 0;
   out_2254906336766818445[46] = 0;
   out_2254906336766818445[47] = 0;
   out_2254906336766818445[48] = 0;
   out_2254906336766818445[49] = 0;
   out_2254906336766818445[50] = 0;
   out_2254906336766818445[51] = 0;
   out_2254906336766818445[52] = 0;
   out_2254906336766818445[53] = 0;
}
void h_14(double *state, double *unused, double *out_1552114113674913175) {
   out_1552114113674913175[0] = state[6];
   out_1552114113674913175[1] = state[7];
   out_1552114113674913175[2] = state[8];
}
void H_14(double *state, double *unused, double *out_3005873367773970173) {
   out_3005873367773970173[0] = 0;
   out_3005873367773970173[1] = 0;
   out_3005873367773970173[2] = 0;
   out_3005873367773970173[3] = 0;
   out_3005873367773970173[4] = 0;
   out_3005873367773970173[5] = 0;
   out_3005873367773970173[6] = 1;
   out_3005873367773970173[7] = 0;
   out_3005873367773970173[8] = 0;
   out_3005873367773970173[9] = 0;
   out_3005873367773970173[10] = 0;
   out_3005873367773970173[11] = 0;
   out_3005873367773970173[12] = 0;
   out_3005873367773970173[13] = 0;
   out_3005873367773970173[14] = 0;
   out_3005873367773970173[15] = 0;
   out_3005873367773970173[16] = 0;
   out_3005873367773970173[17] = 0;
   out_3005873367773970173[18] = 0;
   out_3005873367773970173[19] = 0;
   out_3005873367773970173[20] = 0;
   out_3005873367773970173[21] = 0;
   out_3005873367773970173[22] = 0;
   out_3005873367773970173[23] = 0;
   out_3005873367773970173[24] = 0;
   out_3005873367773970173[25] = 1;
   out_3005873367773970173[26] = 0;
   out_3005873367773970173[27] = 0;
   out_3005873367773970173[28] = 0;
   out_3005873367773970173[29] = 0;
   out_3005873367773970173[30] = 0;
   out_3005873367773970173[31] = 0;
   out_3005873367773970173[32] = 0;
   out_3005873367773970173[33] = 0;
   out_3005873367773970173[34] = 0;
   out_3005873367773970173[35] = 0;
   out_3005873367773970173[36] = 0;
   out_3005873367773970173[37] = 0;
   out_3005873367773970173[38] = 0;
   out_3005873367773970173[39] = 0;
   out_3005873367773970173[40] = 0;
   out_3005873367773970173[41] = 0;
   out_3005873367773970173[42] = 0;
   out_3005873367773970173[43] = 0;
   out_3005873367773970173[44] = 1;
   out_3005873367773970173[45] = 0;
   out_3005873367773970173[46] = 0;
   out_3005873367773970173[47] = 0;
   out_3005873367773970173[48] = 0;
   out_3005873367773970173[49] = 0;
   out_3005873367773970173[50] = 0;
   out_3005873367773970173[51] = 0;
   out_3005873367773970173[52] = 0;
   out_3005873367773970173[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_6672914167572980790) {
  err_fun(nom_x, delta_x, out_6672914167572980790);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7750354326522111493) {
  inv_err_fun(nom_x, true_x, out_7750354326522111493);
}
void pose_H_mod_fun(double *state, double *out_839860879621378337) {
  H_mod_fun(state, out_839860879621378337);
}
void pose_f_fun(double *state, double dt, double *out_4259182462982083528) {
  f_fun(state,  dt, out_4259182462982083528);
}
void pose_F_fun(double *state, double dt, double *out_3243909512724105051) {
  F_fun(state,  dt, out_3243909512724105051);
}
void pose_h_4(double *state, double *unused, double *out_4501441890577505558) {
  h_4(state, unused, out_4501441890577505558);
}
void pose_H_4(double *state, double *unused, double *out_957367488565514356) {
  H_4(state, unused, out_957367488565514356);
}
void pose_h_10(double *state, double *unused, double *out_4701543042744826127) {
  h_10(state, unused, out_4701543042744826127);
}
void pose_H_10(double *state, double *unused, double *out_1475315339015463538) {
  H_10(state, unused, out_1475315339015463538);
}
void pose_h_13(double *state, double *unused, double *out_8766901177225402962) {
  h_13(state, unused, out_8766901177225402962);
}
void pose_H_13(double *state, double *unused, double *out_2254906336766818445) {
  H_13(state, unused, out_2254906336766818445);
}
void pose_h_14(double *state, double *unused, double *out_1552114113674913175) {
  h_14(state, unused, out_1552114113674913175);
}
void pose_H_14(double *state, double *unused, double *out_3005873367773970173) {
  H_14(state, unused, out_3005873367773970173);
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
