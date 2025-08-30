/**
 * 表格组件
 */

// import React from 'react';
import { Table as AntTable, TableProps as AntTableProps } from 'antd';
import { TableColumn } from '@/types';
import classNames from 'classnames';
import './style.scss';

export interface TableProps<T = any> extends Omit<AntTableProps<T>, 'columns'> {
  /** 表格列配置 */
  columns: TableColumn<T>[];
  /** 表格数据 */
  dataSource?: T[];
  /** 是否显示边框 */
  bordered?: boolean;
  /** 表格尺寸 */
  size?: 'small' | 'middle' | 'large';
  /** 是否显示斑马纹 */
  striped?: boolean;
  /** 自定义类名 */
  className?: string;
}

const Table = <T extends Record<string, any>>({
  columns,
  dataSource = [],
  bordered = true,
  size = 'middle',
  striped = false,
  className,
  ...props
}: TableProps<T>) => {
  const tableClass = classNames(
    'qt-table',
    `qt-table--${size}`,
    {
      'qt-table--striped': striped,
    },
    className
  );

  // 转换列配置
  const antColumns = columns.map((col) => ({
    key: col.key,
    title: col.title,
    dataIndex: col.dataIndex as any,
    render: col.render,
    width: col.width,
    align: col.align,
    sorter: col.sorter,
    filters: col.filters,
    fixed: col.fixed,
  }));

  return (
    <AntTable<T>
      {...props}
      columns={antColumns}
      dataSource={dataSource}
      bordered={bordered}
      size={size}
      className={tableClass}
      scroll={{ x: 'max-content' }}
      pagination={{
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) =>
          `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        ...props.pagination,
      }}
    />
  );
};

export default Table;