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
void err_fun(double *nom_x, double *delta_x, double *out_1751486852151240052) {
   out_1751486852151240052[0] = delta_x[0] + nom_x[0];
   out_1751486852151240052[1] = delta_x[1] + nom_x[1];
   out_1751486852151240052[2] = delta_x[2] + nom_x[2];
   out_1751486852151240052[3] = delta_x[3] + nom_x[3];
   out_1751486852151240052[4] = delta_x[4] + nom_x[4];
   out_1751486852151240052[5] = delta_x[5] + nom_x[5];
   out_1751486852151240052[6] = delta_x[6] + nom_x[6];
   out_1751486852151240052[7] = delta_x[7] + nom_x[7];
   out_1751486852151240052[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1850991408901040443) {
   out_1850991408901040443[0] = -nom_x[0] + true_x[0];
   out_1850991408901040443[1] = -nom_x[1] + true_x[1];
   out_1850991408901040443[2] = -nom_x[2] + true_x[2];
   out_1850991408901040443[3] = -nom_x[3] + true_x[3];
   out_1850991408901040443[4] = -nom_x[4] + true_x[4];
   out_1850991408901040443[5] = -nom_x[5] + true_x[5];
   out_1850991408901040443[6] = -nom_x[6] + true_x[6];
   out_1850991408901040443[7] = -nom_x[7] + true_x[7];
   out_1850991408901040443[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_4081979560919394148) {
   out_4081979560919394148[0] = 1.0;
   out_4081979560919394148[1] = 0.0;
   out_4081979560919394148[2] = 0.0;
   out_4081979560919394148[3] = 0.0;
   out_4081979560919394148[4] = 0.0;
   out_4081979560919394148[5] = 0.0;
   out_4081979560919394148[6] = 0.0;
   out_4081979560919394148[7] = 0.0;
   out_4081979560919394148[8] = 0.0;
   out_4081979560919394148[9] = 0.0;
   out_4081979560919394148[10] = 1.0;
   out_4081979560919394148[11] = 0.0;
   out_4081979560919394148[12] = 0.0;
   out_4081979560919394148[13] = 0.0;
   out_4081979560919394148[14] = 0.0;
   out_4081979560919394148[15] = 0.0;
   out_4081979560919394148[16] = 0.0;
   out_4081979560919394148[17] = 0.0;
   out_4081979560919394148[18] = 0.0;
   out_4081979560919394148[19] = 0.0;
   out_4081979560919394148[20] = 1.0;
   out_4081979560919394148[21] = 0.0;
   out_4081979560919394148[22] = 0.0;
   out_4081979560919394148[23] = 0.0;
   out_4081979560919394148[24] = 0.0;
   out_4081979560919394148[25] = 0.0;
   out_4081979560919394148[26] = 0.0;
   out_4081979560919394148[27] = 0.0;
   out_4081979560919394148[28] = 0.0;
   out_4081979560919394148[29] = 0.0;
   out_4081979560919394148[30] = 1.0;
   out_4081979560919394148[31] = 0.0;
   out_4081979560919394148[32] = 0.0;
   out_4081979560919394148[33] = 0.0;
   out_4081979560919394148[34] = 0.0;
   out_4081979560919394148[35] = 0.0;
   out_4081979560919394148[36] = 0.0;
   out_4081979560919394148[37] = 0.0;
   out_4081979560919394148[38] = 0.0;
   out_4081979560919394148[39] = 0.0;
   out_4081979560919394148[40] = 1.0;
   out_4081979560919394148[41] = 0.0;
   out_4081979560919394148[42] = 0.0;
   out_4081979560919394148[43] = 0.0;
   out_4081979560919394148[44] = 0.0;
   out_4081979560919394148[45] = 0.0;
   out_4081979560919394148[46] = 0.0;
   out_4081979560919394148[47] = 0.0;
   out_4081979560919394148[48] = 0.0;
   out_4081979560919394148[49] = 0.0;
   out_4081979560919394148[50] = 1.0;
   out_4081979560919394148[51] = 0.0;
   out_4081979560919394148[52] = 0.0;
   out_4081979560919394148[53] = 0.0;
   out_4081979560919394148[54] = 0.0;
   out_4081979560919394148[55] = 0.0;
   out_4081979560919394148[56] = 0.0;
   out_4081979560919394148[57] = 0.0;
   out_4081979560919394148[58] = 0.0;
   out_4081979560919394148[59] = 0.0;
   out_4081979560919394148[60] = 1.0;
   out_4081979560919394148[61] = 0.0;
   out_4081979560919394148[62] = 0.0;
   out_4081979560919394148[63] = 0.0;
   out_4081979560919394148[64] = 0.0;
   out_4081979560919394148[65] = 0.0;
   out_4081979560919394148[66] = 0.0;
   out_4081979560919394148[67] = 0.0;
   out_4081979560919394148[68] = 0.0;
   out_4081979560919394148[69] = 0.0;
   out_4081979560919394148[70] = 1.0;
   out_4081979560919394148[71] = 0.0;
   out_4081979560919394148[72] = 0.0;
   out_4081979560919394148[73] = 0.0;
   out_4081979560919394148[74] = 0.0;
   out_4081979560919394148[75] = 0.0;
   out_4081979560919394148[76] = 0.0;
   out_4081979560919394148[77] = 0.0;
   out_4081979560919394148[78] = 0.0;
   out_4081979560919394148[79] = 0.0;
   out_4081979560919394148[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_436561100979424394) {
   out_436561100979424394[0] = state[0];
   out_436561100979424394[1] = state[1];
   out_436561100979424394[2] = state[2];
   out_436561100979424394[3] = state[3];
   out_436561100979424394[4] = state[4];
   out_436561100979424394[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_436561100979424394[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_436561100979424394[7] = state[7];
   out_436561100979424394[8] = state[8];
}
void F_fun(double *state, double dt, double *out_212313505569631284) {
   out_212313505569631284[0] = 1;
   out_212313505569631284[1] = 0;
   out_212313505569631284[2] = 0;
   out_212313505569631284[3] = 0;
   out_212313505569631284[4] = 0;
   out_212313505569631284[5] = 0;
   out_212313505569631284[6] = 0;
   out_212313505569631284[7] = 0;
   out_212313505569631284[8] = 0;
   out_212313505569631284[9] = 0;
   out_212313505569631284[10] = 1;
   out_212313505569631284[11] = 0;
   out_212313505569631284[12] = 0;
   out_212313505569631284[13] = 0;
   out_212313505569631284[14] = 0;
   out_212313505569631284[15] = 0;
   out_212313505569631284[16] = 0;
   out_212313505569631284[17] = 0;
   out_212313505569631284[18] = 0;
   out_212313505569631284[19] = 0;
   out_212313505569631284[20] = 1;
   out_212313505569631284[21] = 0;
   out_212313505569631284[22] = 0;
   out_212313505569631284[23] = 0;
   out_212313505569631284[24] = 0;
   out_212313505569631284[25] = 0;
   out_212313505569631284[26] = 0;
   out_212313505569631284[27] = 0;
   out_212313505569631284[28] = 0;
   out_212313505569631284[29] = 0;
   out_212313505569631284[30] = 1;
   out_212313505569631284[31] = 0;
   out_212313505569631284[32] = 0;
   out_212313505569631284[33] = 0;
   out_212313505569631284[34] = 0;
   out_212313505569631284[35] = 0;
   out_212313505569631284[36] = 0;
   out_212313505569631284[37] = 0;
   out_212313505569631284[38] = 0;
   out_212313505569631284[39] = 0;
   out_212313505569631284[40] = 1;
   out_212313505569631284[41] = 0;
   out_212313505569631284[42] = 0;
   out_212313505569631284[43] = 0;
   out_212313505569631284[44] = 0;
   out_212313505569631284[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_212313505569631284[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_212313505569631284[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_212313505569631284[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_212313505569631284[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_212313505569631284[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_212313505569631284[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_212313505569631284[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_212313505569631284[53] = -9.8100000000000005*dt;
   out_212313505569631284[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_212313505569631284[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_212313505569631284[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_212313505569631284[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_212313505569631284[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_212313505569631284[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_212313505569631284[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_212313505569631284[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_212313505569631284[62] = 0;
   out_212313505569631284[63] = 0;
   out_212313505569631284[64] = 0;
   out_212313505569631284[65] = 0;
   out_212313505569631284[66] = 0;
   out_212313505569631284[67] = 0;
   out_212313505569631284[68] = 0;
   out_212313505569631284[69] = 0;
   out_212313505569631284[70] = 1;
   out_212313505569631284[71] = 0;
   out_212313505569631284[72] = 0;
   out_212313505569631284[73] = 0;
   out_212313505569631284[74] = 0;
   out_212313505569631284[75] = 0;
   out_212313505569631284[76] = 0;
   out_212313505569631284[77] = 0;
   out_212313505569631284[78] = 0;
   out_212313505569631284[79] = 0;
   out_212313505569631284[80] = 1;
}
void h_25(double *state, double *unused, double *out_6165914736993252692) {
   out_6165914736993252692[0] = state[6];
}
void H_25(double *state, double *unused, double *out_5111208664992843089) {
   out_5111208664992843089[0] = 0;
   out_5111208664992843089[1] = 0;
   out_5111208664992843089[2] = 0;
   out_5111208664992843089[3] = 0;
   out_5111208664992843089[4] = 0;
   out_5111208664992843089[5] = 0;
   out_5111208664992843089[6] = 1;
   out_5111208664992843089[7] = 0;
   out_5111208664992843089[8] = 0;
}
void h_24(double *state, double *unused, double *out_168543763410584641) {
   out_168543763410584641[0] = state[4];
   out_168543763410584641[1] = state[5];
}
void H_24(double *state, double *unused, double *out_7283858263998342655) {
   out_7283858263998342655[0] = 0;
   out_7283858263998342655[1] = 0;
   out_7283858263998342655[2] = 0;
   out_7283858263998342655[3] = 0;
   out_7283858263998342655[4] = 1;
   out_7283858263998342655[5] = 0;
   out_7283858263998342655[6] = 0;
   out_7283858263998342655[7] = 0;
   out_7283858263998342655[8] = 0;
   out_7283858263998342655[9] = 0;
   out_7283858263998342655[10] = 0;
   out_7283858263998342655[11] = 0;
   out_7283858263998342655[12] = 0;
   out_7283858263998342655[13] = 0;
   out_7283858263998342655[14] = 1;
   out_7283858263998342655[15] = 0;
   out_7283858263998342655[16] = 0;
   out_7283858263998342655[17] = 0;
}
void h_30(double *state, double *unused, double *out_5509994110365947988) {
   out_5509994110365947988[0] = state[4];
}
void H_30(double *state, double *unused, double *out_1805481676498773666) {
   out_1805481676498773666[0] = 0;
   out_1805481676498773666[1] = 0;
   out_1805481676498773666[2] = 0;
   out_1805481676498773666[3] = 0;
   out_1805481676498773666[4] = 1;
   out_1805481676498773666[5] = 0;
   out_1805481676498773666[6] = 0;
   out_1805481676498773666[7] = 0;
   out_1805481676498773666[8] = 0;
}
void h_26(double *state, double *unused, double *out_508320842705102343) {
   out_508320842705102343[0] = state[7];
}
void H_26(double *state, double *unused, double *out_8852711983866899313) {
   out_8852711983866899313[0] = 0;
   out_8852711983866899313[1] = 0;
   out_8852711983866899313[2] = 0;
   out_8852711983866899313[3] = 0;
   out_8852711983866899313[4] = 0;
   out_8852711983866899313[5] = 0;
   out_8852711983866899313[6] = 0;
   out_8852711983866899313[7] = 1;
   out_8852711983866899313[8] = 0;
}
void h_27(double *state, double *unused, double *out_7856362571728933652) {
   out_7856362571728933652[0] = state[3];
}
void H_27(double *state, double *unused, double *out_369281635301651245) {
   out_369281635301651245[0] = 0;
   out_369281635301651245[1] = 0;
   out_369281635301651245[2] = 0;
   out_369281635301651245[3] = 1;
   out_369281635301651245[4] = 0;
   out_369281635301651245[5] = 0;
   out_369281635301651245[6] = 0;
   out_369281635301651245[7] = 0;
   out_369281635301651245[8] = 0;
}
void h_29(double *state, double *unused, double *out_4218913043474911302) {
   out_4218913043474911302[0] = state[1];
}
void H_29(double *state, double *unused, double *out_2082644362171202278) {
   out_2082644362171202278[0] = 0;
   out_2082644362171202278[1] = 1;
   out_2082644362171202278[2] = 0;
   out_2082644362171202278[3] = 0;
   out_2082644362171202278[4] = 0;
   out_2082644362171202278[5] = 0;
   out_2082644362171202278[6] = 0;
   out_2082644362171202278[7] = 0;
   out_2082644362171202278[8] = 0;
}
void h_28(double *state, double *unused, double *out_2657398259586607853) {
   out_2657398259586607853[0] = state[0];
}
void H_28(double *state, double *unused, double *out_7165043379240732852) {
   out_7165043379240732852[0] = 1;
   out_7165043379240732852[1] = 0;
   out_7165043379240732852[2] = 0;
   out_7165043379240732852[3] = 0;
   out_7165043379240732852[4] = 0;
   out_7165043379240732852[5] = 0;
   out_7165043379240732852[6] = 0;
   out_7165043379240732852[7] = 0;
   out_7165043379240732852[8] = 0;
}
void h_31(double *state, double *unused, double *out_1727024757891270667) {
   out_1727024757891270667[0] = state[8];
}
void H_31(double *state, double *unused, double *out_5080562703115882661) {
   out_5080562703115882661[0] = 0;
   out_5080562703115882661[1] = 0;
   out_5080562703115882661[2] = 0;
   out_5080562703115882661[3] = 0;
   out_5080562703115882661[4] = 0;
   out_5080562703115882661[5] = 0;
   out_5080562703115882661[6] = 0;
   out_5080562703115882661[7] = 0;
   out_5080562703115882661[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_1751486852151240052) {
  err_fun(nom_x, delta_x, out_1751486852151240052);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1850991408901040443) {
  inv_err_fun(nom_x, true_x, out_1850991408901040443);
}
void car_H_mod_fun(double *state, double *out_4081979560919394148) {
  H_mod_fun(state, out_4081979560919394148);
}
void car_f_fun(double *state, double dt, double *out_436561100979424394) {
  f_fun(state,  dt, out_436561100979424394);
}
void car_F_fun(double *state, double dt, double *out_212313505569631284) {
  F_fun(state,  dt, out_212313505569631284);
}
void car_h_25(double *state, double *unused, double *out_6165914736993252692) {
  h_25(state, unused, out_6165914736993252692);
}
void car_H_25(double *state, double *unused, double *out_5111208664992843089) {
  H_25(state, unused, out_5111208664992843089);
}
void car_h_24(double *state, double *unused, double *out_168543763410584641) {
  h_24(state, unused, out_168543763410584641);
}
void car_H_24(double *state, double *unused, double *out_7283858263998342655) {
  H_24(state, unused, out_7283858263998342655);
}
void car_h_30(double *state, double *unused, double *out_5509994110365947988) {
  h_30(state, unused, out_5509994110365947988);
}
void car_H_30(double *state, double *unused, double *out_1805481676498773666) {
  H_30(state, unused, out_1805481676498773666);
}
void car_h_26(double *state, double *unused, double *out_508320842705102343) {
  h_26(state, unused, out_508320842705102343);
}
void car_H_26(double *state, double *unused, double *out_8852711983866899313) {
  H_26(state, unused, out_8852711983866899313);
}
void car_h_27(double *state, double *unused, double *out_7856362571728933652) {
  h_27(state, unused, out_7856362571728933652);
}
void car_H_27(double *state, double *unused, double *out_369281635301651245) {
  H_27(state, unused, out_369281635301651245);
}
void car_h_29(double *state, double *unused, double *out_4218913043474911302) {
  h_29(state, unused, out_4218913043474911302);
}
void car_H_29(double *state, double *unused, double *out_2082644362171202278) {
  H_29(state, unused, out_2082644362171202278);
}
void car_h_28(double *state, double *unused, double *out_2657398259586607853) {
  h_28(state, unused, out_2657398259586607853);
}
void car_H_28(double *state, double *unused, double *out_7165043379240732852) {
  H_28(state, unused, out_7165043379240732852);
}
void car_h_31(double *state, double *unused, double *out_1727024757891270667) {
  h_31(state, unused, out_1727024757891270667);
}
void car_H_31(double *state, double *unused, double *out_5080562703115882661) {
  H_31(state, unused, out_5080562703115882661);
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
