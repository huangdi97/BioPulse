/// Represents a field visit record by a sales representative.
///
/// Tracks interactions with healthcare professionals (HCPs) including
/// visit details, compliance status, and promoted products.
class Visit {
  final int? id;
  final String hcpName;
  final String hospital;
  final String? department;
  final String visitDate;
  final String visitType;
  final String status;
  final String? notes;
  final String? complianceStatus;
  final String? products;

  const Visit({
    this.id,
    required this.hcpName,
    required this.hospital,
    this.department,
    required this.visitDate,
    required this.visitType,
    this.status = 'pending',
    this.notes,
    this.complianceStatus,
    this.products,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'hcp_name': hcpName,
      'hospital': hospital,
      'department': department,
      'visit_date': visitDate,
      'visit_type': visitType,
      'status': status,
      'notes': notes,
      'compliance_status': complianceStatus,
      'products': products,
    };
  }

  factory Visit.fromMap(Map<String, dynamic> map) {
    return Visit(
      id: map['id'] as int?,
      hcpName: map['hcp_name'] as String,
      hospital: map['hospital'] as String,
      department: map['department'] as String?,
      visitDate: map['visit_date'] as String,
      visitType: map['visit_type'] as String,
      status: map['status'] as String? ?? 'pending',
      notes: map['notes'] as String?,
      complianceStatus: map['compliance_status'] as String?,
      products: map['products'] as String?,
    );
  }

  Visit copyWith({
    int? id,
    String? hcpName,
    String? hospital,
    String? department,
    String? visitDate,
    String? visitType,
    String? status,
    String? notes,
    String? complianceStatus,
    String? products,
  }) {
    return Visit(
      id: id ?? this.id,
      hcpName: hcpName ?? this.hcpName,
      hospital: hospital ?? this.hospital,
      department: department ?? this.department,
      visitDate: visitDate ?? this.visitDate,
      visitType: visitType ?? this.visitType,
      status: status ?? this.status,
      notes: notes ?? this.notes,
      complianceStatus: complianceStatus ?? this.complianceStatus,
      products: products ?? this.products,
    );
  }
}
