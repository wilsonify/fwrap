subroutine arr_args_c(assumed_size_d1, assumed_size_d2, assumed_size, d1, assumed_shape_d1, assumed_shape_d2, assumed_shape, explicit_shape_d1, explicit_shape_d2, explicit_shape, c1, c2, fw_iserr__, fw_errstr__) bind(c, name="arr_args_c")
     use fwrap_ktp_mod
     implicit none
     integer(kind=fwi_npy_intp_t), intent(in) :: assumed_size_d1
     integer(kind=fwi_npy_intp_t), intent(in) :: assumed_size_d2
     integer(kind=fwi_integer_t), dimension(assumed_size_d1, assumed_size_d2), intent(inout) :: assumed_size
     integer(kind=fwi_integer_t), intent(in) :: d1
     integer(kind=fwi_npy_intp_t), intent(in) :: assumed_shape_d1
     integer(kind=fwi_npy_intp_t), intent(in) :: assumed_shape_d2
     logical(kind=fwl_logical_t), dimension(assumed_shape_d1, assumed_shape_d2), intent(out) :: assumed_shape
     integer(kind=fwi_npy_intp_t), intent(in) :: explicit_shape_d1
     integer(kind=fwi_npy_intp_t), intent(in) :: explicit_shape_d2
     complex(kind=fwc_complex_t), dimension(explicit_shape_d1, explicit_shape_d2), intent(inout) :: explicit_shape
     integer(kind=fwi_integer_t), intent(inout) :: c1
     integer(kind=fwi_integer_t) :: c2
     integer(kind=fwi_integer_t), intent(out) :: fw_iserr__
     character(kind=fw_character_t, len=1), dimension(fw_errstr_len) :: fw_errstr__
     interface
         subroutine arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
             use fwrap_ktp_mod
             implicit none
             integer(kind=fwi_integer_t), dimension(d1, *), intent(inout) :: assumed_size
             integer(kind=fwi_integer_t), intent(in) :: d1
             logical(kind=fwl_logical_t), dimension(:, :), intent(out) :: assumed_shape
             complex(kind=fwc_complex_t), dimension(c1, c2), intent(inout) :: explicit_shape
             integer(kind=fwi_integer_t), intent(inout) :: c1
             integer(kind=fwi_integer_t) :: c2
         end subroutine arr_args
     end interface
     fw_iserr__ = FW_INIT_ERR__
     if ((d1) .ne. (assumed_size_d1)) then
         fw_iserr__ = FW_ARR_DIM__
         fw_errstr__ = transfer("assumed_size                                                   ", fw_errstr__)
         fw_errstr__(fw_errstr_len) = C_NULL_CHAR
         return
     endif
     if ((c1) .ne. (explicit_shape_d1) .or. (c2) .ne. (explicit_shape_d2)) then
         fw_iserr__ = FW_ARR_DIM__
         fw_errstr__ = transfer("explicit_shape                                                 ", fw_errstr__)
         fw_errstr__(fw_errstr_len) = C_NULL_CHAR
         return
     endif
     call arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
     fw_iserr__ = FW_NO_ERR__
end subroutine arr_args_c
