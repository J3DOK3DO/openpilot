#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_7316368395552197740) {
   out_7316368395552197740[0] = delta_x[0] + nom_x[0];
   out_7316368395552197740[1] = delta_x[1] + nom_x[1];
   out_7316368395552197740[2] = delta_x[2] + nom_x[2];
   out_7316368395552197740[3] = delta_x[3] + nom_x[3];
   out_7316368395552197740[4] = delta_x[4] + nom_x[4];
   out_7316368395552197740[5] = delta_x[5] + nom_x[5];
   out_7316368395552197740[6] = delta_x[6] + nom_x[6];
   out_7316368395552197740[7] = delta_x[7] + nom_x[7];
   out_7316368395552197740[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1979647693272640270) {
   out_1979647693272640270[0] = -nom_x[0] + true_x[0];
   out_1979647693272640270[1] = -nom_x[1] + true_x[1];
   out_1979647693272640270[2] = -nom_x[2] + true_x[2];
   out_1979647693272640270[3] = -nom_x[3] + true_x[3];
   out_1979647693272640270[4] = -nom_x[4] + true_x[4];
   out_1979647693272640270[5] = -nom_x[5] + true_x[5];
   out_1979647693272640270[6] = -nom_x[6] + true_x[6];
   out_1979647693272640270[7] = -nom_x[7] + true_x[7];
   out_1979647693272640270[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_2820666923051649688) {
   out_2820666923051649688[0] = 1.0;
   out_2820666923051649688[1] = 0.0;
   out_2820666923051649688[2] = 0.0;
   out_2820666923051649688[3] = 0.0;
   out_2820666923051649688[4] = 0.0;
   out_2820666923051649688[5] = 0.0;
   out_2820666923051649688[6] = 0.0;
   out_2820666923051649688[7] = 0.0;
   out_2820666923051649688[8] = 0.0;
   out_2820666923051649688[9] = 0.0;
   out_2820666923051649688[10] = 1.0;
   out_2820666923051649688[11] = 0.0;
   out_2820666923051649688[12] = 0.0;
   out_2820666923051649688[13] = 0.0;
   out_2820666923051649688[14] = 0.0;
   out_2820666923051649688[15] = 0.0;
   out_2820666923051649688[16] = 0.0;
   out_2820666923051649688[17] = 0.0;
   out_2820666923051649688[18] = 0.0;
   out_2820666923051649688[19] = 0.0;
   out_2820666923051649688[20] = 1.0;
   out_2820666923051649688[21] = 0.0;
   out_2820666923051649688[22] = 0.0;
   out_2820666923051649688[23] = 0.0;
   out_2820666923051649688[24] = 0.0;
   out_2820666923051649688[25] = 0.0;
   out_2820666923051649688[26] = 0.0;
   out_2820666923051649688[27] = 0.0;
   out_2820666923051649688[28] = 0.0;
   out_2820666923051649688[29] = 0.0;
   out_2820666923051649688[30] = 1.0;
   out_2820666923051649688[31] = 0.0;
   out_2820666923051649688[32] = 0.0;
   out_2820666923051649688[33] = 0.0;
   out_2820666923051649688[34] = 0.0;
   out_2820666923051649688[35] = 0.0;
   out_2820666923051649688[36] = 0.0;
   out_2820666923051649688[37] = 0.0;
   out_2820666923051649688[38] = 0.0;
   out_2820666923051649688[39] = 0.0;
   out_2820666923051649688[40] = 1.0;
   out_2820666923051649688[41] = 0.0;
   out_2820666923051649688[42] = 0.0;
   out_2820666923051649688[43] = 0.0;
   out_2820666923051649688[44] = 0.0;
   out_2820666923051649688[45] = 0.0;
   out_2820666923051649688[46] = 0.0;
   out_2820666923051649688[47] = 0.0;
   out_2820666923051649688[48] = 0.0;
   out_2820666923051649688[49] = 0.0;
   out_2820666923051649688[50] = 1.0;
   out_2820666923051649688[51] = 0.0;
   out_2820666923051649688[52] = 0.0;
   out_2820666923051649688[53] = 0.0;
   out_2820666923051649688[54] = 0.0;
   out_2820666923051649688[55] = 0.0;
   out_2820666923051649688[56] = 0.0;
   out_2820666923051649688[57] = 0.0;
   out_2820666923051649688[58] = 0.0;
   out_2820666923051649688[59] = 0.0;
   out_2820666923051649688[60] = 1.0;
   out_2820666923051649688[61] = 0.0;
   out_2820666923051649688[62] = 0.0;
   out_2820666923051649688[63] = 0.0;
   out_2820666923051649688[64] = 0.0;
   out_2820666923051649688[65] = 0.0;
   out_2820666923051649688[66] = 0.0;
   out_2820666923051649688[67] = 0.0;
   out_2820666923051649688[68] = 0.0;
   out_2820666923051649688[69] = 0.0;
   out_2820666923051649688[70] = 1.0;
   out_2820666923051649688[71] = 0.0;
   out_2820666923051649688[72] = 0.0;
   out_2820666923051649688[73] = 0.0;
   out_2820666923051649688[74] = 0.0;
   out_2820666923051649688[75] = 0.0;
   out_2820666923051649688[76] = 0.0;
   out_2820666923051649688[77] = 0.0;
   out_2820666923051649688[78] = 0.0;
   out_2820666923051649688[79] = 0.0;
   out_2820666923051649688[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_830938017298167130) {
   out_830938017298167130[0] = state[0];
   out_830938017298167130[1] = state[1];
   out_830938017298167130[2] = state[2];
   out_830938017298167130[3] = state[3];
   out_830938017298167130[4] = state[4];
   out_830938017298167130[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_830938017298167130[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_830938017298167130[7] = state[7];
   out_830938017298167130[8] = state[8];
}
void F_fun(double *state, double dt, double *out_8851408027615256561) {
   out_8851408027615256561[0] = 1;
   out_8851408027615256561[1] = 0;
   out_8851408027615256561[2] = 0;
   out_8851408027615256561[3] = 0;
   out_8851408027615256561[4] = 0;
   out_8851408027615256561[5] = 0;
   out_8851408027615256561[6] = 0;
   out_8851408027615256561[7] = 0;
   out_8851408027615256561[8] = 0;
   out_8851408027615256561[9] = 0;
   out_8851408027615256561[10] = 1;
   out_8851408027615256561[11] = 0;
   out_8851408027615256561[12] = 0;
   out_8851408027615256561[13] = 0;
   out_8851408027615256561[14] = 0;
   out_8851408027615256561[15] = 0;
   out_8851408027615256561[16] = 0;
   out_8851408027615256561[17] = 0;
   out_8851408027615256561[18] = 0;
   out_8851408027615256561[19] = 0;
   out_8851408027615256561[20] = 1;
   out_8851408027615256561[21] = 0;
   out_8851408027615256561[22] = 0;
   out_8851408027615256561[23] = 0;
   out_8851408027615256561[24] = 0;
   out_8851408027615256561[25] = 0;
   out_8851408027615256561[26] = 0;
   out_8851408027615256561[27] = 0;
   out_8851408027615256561[28] = 0;
   out_8851408027615256561[29] = 0;
   out_8851408027615256561[30] = 1;
   out_8851408027615256561[31] = 0;
   out_8851408027615256561[32] = 0;
   out_8851408027615256561[33] = 0;
   out_8851408027615256561[34] = 0;
   out_8851408027615256561[35] = 0;
   out_8851408027615256561[36] = 0;
   out_8851408027615256561[37] = 0;
   out_8851408027615256561[38] = 0;
   out_8851408027615256561[39] = 0;
   out_8851408027615256561[40] = 1;
   out_8851408027615256561[41] = 0;
   out_8851408027615256561[42] = 0;
   out_8851408027615256561[43] = 0;
   out_8851408027615256561[44] = 0;
   out_8851408027615256561[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_8851408027615256561[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_8851408027615256561[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_8851408027615256561[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_8851408027615256561[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_8851408027615256561[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_8851408027615256561[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_8851408027615256561[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_8851408027615256561[53] = -9.8100000000000005*dt;
   out_8851408027615256561[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_8851408027615256561[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_8851408027615256561[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8851408027615256561[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8851408027615256561[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_8851408027615256561[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_8851408027615256561[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_8851408027615256561[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8851408027615256561[62] = 0;
   out_8851408027615256561[63] = 0;
   out_8851408027615256561[64] = 0;
   out_8851408027615256561[65] = 0;
   out_8851408027615256561[66] = 0;
   out_8851408027615256561[67] = 0;
   out_8851408027615256561[68] = 0;
   out_8851408027615256561[69] = 0;
   out_8851408027615256561[70] = 1;
   out_8851408027615256561[71] = 0;
   out_8851408027615256561[72] = 0;
   out_8851408027615256561[73] = 0;
   out_8851408027615256561[74] = 0;
   out_8851408027615256561[75] = 0;
   out_8851408027615256561[76] = 0;
   out_8851408027615256561[77] = 0;
   out_8851408027615256561[78] = 0;
   out_8851408027615256561[79] = 0;
   out_8851408027615256561[80] = 1;
}
void h_25(double *state, double *unused, double *out_7795708739304550937) {
   out_7795708739304550937[0] = state[6];
}
void H_25(double *state, double *unused, double *out_7724358748236314528) {
   out_7724358748236314528[0] = 0;
   out_7724358748236314528[1] = 0;
   out_7724358748236314528[2] = 0;
   out_7724358748236314528[3] = 0;
   out_7724358748236314528[4] = 0;
   out_7724358748236314528[5] = 0;
   out_7724358748236314528[6] = 1;
   out_7724358748236314528[7] = 0;
   out_7724358748236314528[8] = 0;
}
void h_24(double *state, double *unused, double *out_8377130028693208980) {
   out_8377130028693208980[0] = state[4];
   out_8377130028693208980[1] = state[5];
}
void H_24(double *state, double *unused, double *out_8545170901866087115) {
   out_8545170901866087115[0] = 0;
   out_8545170901866087115[1] = 0;
   out_8545170901866087115[2] = 0;
   out_8545170901866087115[3] = 0;
   out_8545170901866087115[4] = 1;
   out_8545170901866087115[5] = 0;
   out_8545170901866087115[6] = 0;
   out_8545170901866087115[7] = 0;
   out_8545170901866087115[8] = 0;
   out_8545170901866087115[9] = 0;
   out_8545170901866087115[10] = 0;
   out_8545170901866087115[11] = 0;
   out_8545170901866087115[12] = 0;
   out_8545170901866087115[13] = 0;
   out_8545170901866087115[14] = 1;
   out_8545170901866087115[15] = 0;
   out_8545170901866087115[16] = 0;
   out_8545170901866087115[17] = 0;
}
void h_30(double *state, double *unused, double *out_1351097608283057666) {
   out_1351097608283057666[0] = state[4];
}
void H_30(double *state, double *unused, double *out_8204052366965988461) {
   out_8204052366965988461[0] = 0;
   out_8204052366965988461[1] = 0;
   out_8204052366965988461[2] = 0;
   out_8204052366965988461[3] = 0;
   out_8204052366965988461[4] = 1;
   out_8204052366965988461[5] = 0;
   out_8204052366965988461[6] = 0;
   out_8204052366965988461[7] = 0;
   out_8204052366965988461[8] = 0;
}
void h_26(double *state, double *unused, double *out_5047943909130791480) {
   out_5047943909130791480[0] = state[7];
}
void H_26(double *state, double *unused, double *out_3982855429362258304) {
   out_3982855429362258304[0] = 0;
   out_3982855429362258304[1] = 0;
   out_3982855429362258304[2] = 0;
   out_3982855429362258304[3] = 0;
   out_3982855429362258304[4] = 0;
   out_3982855429362258304[5] = 0;
   out_3982855429362258304[6] = 0;
   out_3982855429362258304[7] = 1;
   out_3982855429362258304[8] = 0;
}
void h_27(double *state, double *unused, double *out_2569801523469225990) {
   out_2569801523469225990[0] = state[3];
}
void H_27(double *state, double *unused, double *out_1021899106308281419) {
   out_1021899106308281419[0] = 0;
   out_1021899106308281419[1] = 0;
   out_1021899106308281419[2] = 0;
   out_1021899106308281419[3] = 1;
   out_1021899106308281419[4] = 0;
   out_1021899106308281419[5] = 0;
   out_1021899106308281419[6] = 0;
   out_1021899106308281419[7] = 0;
   out_1021899106308281419[8] = 0;
}
void h_29(double *state, double *unused, double *out_2294607461184720101) {
   out_2294607461184720101[0] = state[1];
}
void H_29(double *state, double *unused, double *out_3706893762423098514) {
   out_3706893762423098514[0] = 0;
   out_3706893762423098514[1] = 1;
   out_3706893762423098514[2] = 0;
   out_3706893762423098514[3] = 0;
   out_3706893762423098514[4] = 0;
   out_3706893762423098514[5] = 0;
   out_3706893762423098514[6] = 0;
   out_3706893762423098514[7] = 0;
   out_3706893762423098514[8] = 0;
}
void h_28(double *state, double *unused, double *out_2431871744191619655) {
   out_2431871744191619655[0] = state[0];
}
void H_28(double *state, double *unused, double *out_5670524033988424765) {
   out_5670524033988424765[0] = 1;
   out_5670524033988424765[1] = 0;
   out_5670524033988424765[2] = 0;
   out_5670524033988424765[3] = 0;
   out_5670524033988424765[4] = 0;
   out_5670524033988424765[5] = 0;
   out_5670524033988424765[6] = 0;
   out_5670524033988424765[7] = 0;
   out_5670524033988424765[8] = 0;
}
void h_31(double *state, double *unused, double *out_7013585806150978329) {
   out_7013585806150978329[0] = state[8];
}
void H_31(double *state, double *unused, double *out_3356647327128906828) {
   out_3356647327128906828[0] = 0;
   out_3356647327128906828[1] = 0;
   out_3356647327128906828[2] = 0;
   out_3356647327128906828[3] = 0;
   out_3356647327128906828[4] = 0;
   out_3356647327128906828[5] = 0;
   out_3356647327128906828[6] = 0;
   out_3356647327128906828[7] = 0;
   out_3356647327128906828[8] = 1;
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

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_7316368395552197740) {
  err_fun(nom_x, delta_x, out_7316368395552197740);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1979647693272640270) {
  inv_err_fun(nom_x, true_x, out_1979647693272640270);
}
void car_H_mod_fun(double *state, double *out_2820666923051649688) {
  H_mod_fun(state, out_2820666923051649688);
}
void car_f_fun(double *state, double dt, double *out_830938017298167130) {
  f_fun(state,  dt, out_830938017298167130);
}
void car_F_fun(double *state, double dt, double *out_8851408027615256561) {
  F_fun(state,  dt, out_8851408027615256561);
}
void car_h_25(double *state, double *unused, double *out_7795708739304550937) {
  h_25(state, unused, out_7795708739304550937);
}
void car_H_25(double *state, double *unused, double *out_7724358748236314528) {
  H_25(state, unused, out_7724358748236314528);
}
void car_h_24(double *state, double *unused, double *out_8377130028693208980) {
  h_24(state, unused, out_8377130028693208980);
}
void car_H_24(double *state, double *unused, double *out_8545170901866087115) {
  H_24(state, unused, out_8545170901866087115);
}
void car_h_30(double *state, double *unused, double *out_1351097608283057666) {
  h_30(state, unused, out_1351097608283057666);
}
void car_H_30(double *state, double *unused, double *out_8204052366965988461) {
  H_30(state, unused, out_8204052366965988461);
}
void car_h_26(double *state, double *unused, double *out_5047943909130791480) {
  h_26(state, unused, out_5047943909130791480);
}
void car_H_26(double *state, double *unused, double *out_3982855429362258304) {
  H_26(state, unused, out_3982855429362258304);
}
void car_h_27(double *state, double *unused, double *out_2569801523469225990) {
  h_27(state, unused, out_2569801523469225990);
}
void car_H_27(double *state, double *unused, double *out_1021899106308281419) {
  H_27(state, unused, out_1021899106308281419);
}
void car_h_29(double *state, double *unused, double *out_2294607461184720101) {
  h_29(state, unused, out_2294607461184720101);
}
void car_H_29(double *state, double *unused, double *out_3706893762423098514) {
  H_29(state, unused, out_3706893762423098514);
}
void car_h_28(double *state, double *unused, double *out_2431871744191619655) {
  h_28(state, unused, out_2431871744191619655);
}
void car_H_28(double *state, double *unused, double *out_5670524033988424765) {
  H_28(state, unused, out_5670524033988424765);
}
void car_h_31(double *state, double *unused, double *out_7013585806150978329) {
  h_31(state, unused, out_7013585806150978329);
}
void car_H_31(double *state, double *unused, double *out_3356647327128906828) {
  H_31(state, unused, out_3356647327128906828);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
